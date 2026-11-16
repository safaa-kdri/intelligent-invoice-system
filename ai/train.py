"""
Entraînement du modèle MobileNetV2 pour la classification des factures.

Architecture :
    - MobileNetV2 pré-entraîné sur ImageNet (sans la tête de classification)
    - Tête personnalisée : GlobalAveragePooling2D → Dense(128) → Dropout → Dense(3, softmax)
    - Transfer learning + fine-tuning léger

Entrée  : images 224x224 RGB
Sortie  : 3 classes (facture_achat, facture_vente, autre)

À exécuter : python train.py
"""
import os
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.metrics import classification_report, confusion_matrix


# ==================================================
# CONFIGURATION
# ==================================================
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 15
LEARNING_RATE = 1e-3
FINE_TUNE_AT = 100  # couche à partir de laquelle on fine-tune (sur 154 de MobileNetV2)

CLASSES = ["facture_achat", "facture_vente", "autre"]
NB_CLASSES = len(CLASSES)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODELS_DIR, "mobilenetv2_invoice.h5")
HISTORY_PATH = os.path.join(MODELS_DIR, "training_history.png")
CONFUSION_PATH = os.path.join(MODELS_DIR, "confusion_matrix.png")
METRICS_PATH = os.path.join(MODELS_DIR, "metrics.json")


# ==================================================
# CHARGEMENT DES DONNÉES
# ==================================================
def load_datasets():
    """Charge les 3 datasets (train, val, test) depuis les dossiers."""
    print("Chargement du dataset...")

    train_ds = keras.utils.image_dataset_from_directory(
        os.path.join(DATASET_DIR, "train"),
        labels="inferred",
        label_mode="categorical",
        class_names=CLASSES,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=True,
        seed=42,
    )

    val_ds = keras.utils.image_dataset_from_directory(
        os.path.join(DATASET_DIR, "val"),
        labels="inferred",
        label_mode="categorical",
        class_names=CLASSES,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    test_ds = keras.utils.image_dataset_from_directory(
        os.path.join(DATASET_DIR, "test"),
        labels="inferred",
        label_mode="categorical",
        class_names=CLASSES,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    # Normalisation des pixels (0-255 → -1 à 1, pré-entraînement MobileNetV2)
    normalization_layer = layers.Rescaling(1.0 / 127.5, offset=-1)

    train_ds = train_ds.map(lambda x, y: (normalization_layer(x), y))
    val_ds = val_ds.map(lambda x, y: (normalization_layer(x), y))
    test_ds = test_ds.map(lambda x, y: (normalization_layer(x), y))

    # Performance : préchargement en mémoire
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
    test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)

    return train_ds, val_ds, test_ds


# ==================================================
# CONSTRUCTION DU MODÈLE
# ==================================================
def build_model():
    """Construit le modèle MobileNetV2 + tête personnalisée."""
    print("Construction du modèle...")

    # Charger MobileNetV2 sans la tête de classification
    base_model = keras.applications.MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )

    # Geler le modèle de base (transfer learning étape 1)
    base_model.trainable = False

    # Construire la tête
    inputs = keras.Input(shape=(*IMG_SIZE, 3))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(NB_CLASSES, activation="softmax")(x)

    model = keras.Model(inputs, outputs)

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model, base_model


# ==================================================
# CALLBACKS
# ==================================================
def get_callbacks():
    """Retourne les callbacks pour l'entraînement."""
    return [
        # Sauvegarde le meilleur modèle selon la val_accuracy
        keras.callbacks.ModelCheckpoint(
            MODEL_PATH,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        # Réduit le learning rate si pas d'amélioration
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            verbose=1,
            min_lr=1e-6,
        ),
        # Arrête si pas d'amélioration pendant 5 époques
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
            verbose=1,
        ),
    ]


# ==================================================
# ENTRAÎNEMENT
# ==================================================
def train():
    """Entraîne le modèle en 2 phases : transfer learning puis fine-tuning."""
    train_ds, val_ds, test_ds = load_datasets()
    model, base_model = build_model()

    print("\n" + "=" * 60)
    print("PHASE 1 : Transfer Learning (base gelée)")
    print("=" * 60)

    history1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=get_callbacks(),
        verbose=1,
    )

    print("\n" + "=" * 60)
    print("PHASE 2 : Fine-tuning (dégel des dernières couches)")
    print("=" * 60)

    # Dégeler les dernières couches
    base_model.trainable = True
    for layer in base_model.layers[:FINE_TUNE_AT]:
        layer.trainable = False

    # Recompiler avec un learning rate plus petit
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE / 10),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    history2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=5,
        callbacks=get_callbacks(),
        verbose=1,
    )

    # Fusionner les historiques
    combined_history = {}
    for key in history1.history.keys():
        combined_history[key] = history1.history[key] + history2.history.get(key, [])

    return model, combined_history, test_ds


# ==================================================
# ÉVALUATION
# ==================================================
def evaluate(model, test_ds):
    """Évalue le modèle sur le jeu de test et génère les métriques."""
    print("\n" + "=" * 60)
    print("ÉVALUATION SUR LE JEU DE TEST")
    print("=" * 60)

    # Prédictions
    y_pred_probs = model.predict(test_ds, verbose=0)
    y_pred = np.argmax(y_pred_probs, axis=1)

    # Vraies étiquettes
    y_true = []
    for _, labels in test_ds:
        y_true.extend(np.argmax(labels.numpy(), axis=1))
    y_true = np.array(y_true)

    # Rapport de classification
    report = classification_report(
        y_true, y_pred, target_names=CLASSES, output_dict=True
    )
    print("\nRapport de classification :")
    print(classification_report(y_true, y_pred, target_names=CLASSES))

    # Matrice de confusion
    cm = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=CLASSES, yticklabels=CLASSES,
    )
    plt.title("Matrice de confusion")
    plt.xlabel("Prédit")
    plt.ylabel("Réel")
    plt.tight_layout()
    plt.savefig(CONFUSION_PATH, dpi=100)
    plt.close()
    print(f"\nMatrice de confusion sauvegardée : {CONFUSION_PATH}")

    # Calcul du F1-score global
    f1_macro = report["macro avg"]["f1-score"]
    accuracy = report["accuracy"]

    # Sauvegarder les métriques au format JSON
    metrics = {
        "accuracy": round(float(accuracy), 4),
        "f1_macro": round(float(f1_macro), 4),
        "per_class": {
            cls: {
                "precision": round(report[cls]["precision"], 4),
                "recall": round(report[cls]["recall"], 4),
                "f1_score": round(report[cls]["f1-score"], 4),
                "support": int(report[cls]["support"]),
            }
            for cls in CLASSES
        },
        "confusion_matrix": cm.tolist(),
    }

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(f"\nMétriques sauvegardées : {METRICS_PATH}")

    return metrics


# ==================================================
# GRAPHIQUES
# ==================================================
def plot_training_history(history_dict):
    """Génère les courbes d'apprentissage (loss, accuracy)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Accuracy
    axes[0].plot(history_dict["accuracy"], label="Train", linewidth=2)
    axes[0].plot(history_dict["val_accuracy"], label="Val", linewidth=2)
    axes[0].set_title("Accuracy par époque")
    axes[0].set_xlabel("Époque")
    axes[0].set_ylabel("Accuracy")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Loss
    axes[1].plot(history_dict["loss"], label="Train", linewidth=2)
    axes[1].plot(history_dict["val_loss"], label="Val", linewidth=2)
    axes[1].set_title("Loss par époque")
    axes[1].set_xlabel("Époque")
    axes[1].set_ylabel("Loss")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(HISTORY_PATH, dpi=100)
    plt.close()
    print(f"Courbes d'apprentissage sauvegardées : {HISTORY_PATH}")


# ==================================================
# MAIN
# ==================================================
def main():
    print("=" * 60)
    print("ENTRAÎNEMENT DU MODÈLE CNN - Classification des factures")
    print("=" * 60)
    print(f"Classes      : {CLASSES}")
    print(f"Image size   : {IMG_SIZE}")
    print(f"Batch size   : {BATCH_SIZE}")
    print(f"Epochs       : {EPOCHS} (transfer) + 5 (fine-tuning)")
    print(f"Learning rate: {LEARNING_RATE}")
    print()

    model, history, test_ds = train()

    print("\n" + "=" * 60)
    print("SAUVEGARDE DU MODÈLE FINAL")
    print("=" * 60)
    model.save(MODEL_PATH)
    print(f"✅ Modèle sauvegardé : {MODEL_PATH}")

    # Générer les courbes
    plot_training_history(history)

    # Évaluer
    metrics = evaluate(model, test_ds)

    print("\n" + "=" * 60)
    print("RÉSUMÉ FINAL")
    print("=" * 60)
    print(f"✅ Accuracy globale : {metrics['accuracy'] * 100:.2f}%")
    print(f"✅ F1-score macro   : {metrics['f1_macro'] * 100:.2f}%")
    print("\nPar classe :")
    for cls, m in metrics["per_class"].items():
        print(f"  {cls:15s} : Precision={m['precision']*100:.1f}%  "
              f"Recall={m['recall']*100:.1f}%  F1={m['f1_score']*100:.1f}%")
    print("\n🎉 Entraînement terminé avec succès !")


if __name__ == "__main__":
    main()
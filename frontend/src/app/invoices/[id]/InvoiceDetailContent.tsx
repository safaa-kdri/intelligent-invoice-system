"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Chip,
  CircularProgress,
  Alert,
  AlertTitle,
  Divider,
  Table,
  TableBody,
  TableRow,
  TableCell,
  TextField,
  Snackbar,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import SaveIcon from "@mui/icons-material/Save";
import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningIcon from "@mui/icons-material/Warning";
import ErrorIcon from "@mui/icons-material/Error";
import {
  getInvoiceById,
  deleteInvoice,
  downloadInvoice,
  updateInvoice,
  UpdateInvoicePayload,
  InvoiceResponse,
} from "@/lib/api";

const LABEL_FR: Record<string, string> = {
  facture_achat: "Facture d'achat",
  facture_vente: "Facture de vente",
  autre: "Autre document",
};

const WARNING_FR: Record<string, string> = {
  PIPELINE_IA_NOT_CONNECTED: "Pipeline IA pas encore connecté",
  BLURRY_IMAGE: "Image floue",
  DARK_IMAGE: "Image trop sombre",
  OVEREXPOSED_IMAGE: "Image surexposée",
  SKEWED_IMAGE: "Image inclinée",
  BAD_FRAMING: "Cadrage incorrect",
  AMOUNT_MISMATCH: "HT + TVA ≠ TTC",
  INVALID_DATE: "Date invalide",
  POTENTIAL_DUPLICATE: "Doublon potentiel",
  LOW_CONFIDENCE: "Confiance faible",
  CNN_OVERRIDDEN_BY_OCR: "Corrigé par l'analyse OCR",
  INVOICE_TYPE_UNDETERMINED: "Type achat/vente indéterminé",
};

interface FormData {
  supplier: string;
  invoice_number: string;
  date: string;
  total_ht: string;
  vat: string;
  total_ttc: string;
}

function invoiceToForm(inv: InvoiceResponse): FormData {
  return {
    supplier: inv.extracted.supplier || "",
    invoice_number: inv.extracted.invoice_number || "",
    date: inv.extracted.date || "",
    total_ht: inv.extracted.total_ht !== null ? String(inv.extracted.total_ht) : "",
    vat: inv.extracted.vat !== null ? String(inv.extracted.vat) : "",
    total_ttc: inv.extracted.total_ttc !== null ? String(inv.extracted.total_ttc) : "",
  };
}

function formToPayload(form: FormData): UpdateInvoicePayload {
  return {
    supplier: form.supplier.trim() || null,
    invoice_number: form.invoice_number.trim() || null,
    date: form.date.trim() || null,
    total_ht: form.total_ht.trim() ? parseFloat(form.total_ht) : null,
    vat: form.vat.trim() ? parseFloat(form.vat) : null,
    total_ttc: form.total_ttc.trim() ? parseFloat(form.total_ttc) : null,
  };
}

export default function InvoiceDetailContent() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [invoice, setInvoice] = useState<InvoiceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editMode, setEditMode] = useState(false);
  const [form, setForm] = useState<FormData>({
    supplier: "", invoice_number: "", date: "",
    total_ht: "", vat: "", total_ttc: "",
  });
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchInvoice = async () => {
      setLoading(true);
      try {
        const data = await getInvoiceById(id);
        setInvoice(data);
        setForm(invoiceToForm(data));
      } catch {
        setError(`Impossible de charger la facture #${id}.`);
      } finally {
        setLoading(false);
      }
    };

    if (!isNaN(id)) {
      fetchInvoice();
    }
  }, [id]);

  const handleDelete = async () => {
    if (!confirm(`Supprimer la facture #${id} ? Cette action est irréversible.`)) return;
    try {
      await deleteInvoice(id);
      router.push("/historique");
    } catch {
      alert("Erreur lors de la suppression.");
    }
  };

  const handleEdit = () => {
    if (invoice) {
      setForm(invoiceToForm(invoice));
      setEditMode(true);
    }
  };

  const handleCancel = () => {
    if (invoice) {
      setForm(invoiceToForm(invoice));
    }
    setEditMode(false);
  };

  const handleSave = async () => {
    if (!invoice) return;

    // Validation basique
    if (form.date && !/^\d{4}-\d{2}-\d{2}$/.test(form.date)) {
      alert("La date doit être au format YYYY-MM-DD (ex: 2024-10-11).");
      return;
    }

    setSaving(true);
    try {
      const payload = formToPayload(form);
      const updated = await updateInvoice(invoice.id, payload);
      setInvoice(updated);
      setForm(invoiceToForm(updated));
      setEditMode(false);
      setSuccessMessage("Corrections enregistrées avec succès !");
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { error?: { message?: string } } } };
      const apiError = axiosError.response?.data?.error;
      alert(apiError?.message || "Erreur lors de l'enregistrement.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !invoice) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">{error || "Facture introuvable."}</Alert>
        <Button
          component={Link}
          href="/historique"
          startIcon={<ArrowBackIcon />}
          sx={{ mt: 2 }}
        >
          Retour à l&apos;historique
        </Button>
      </Container>
    );
  }

  const statusBadge = () => {
    if (invoice.status === "processed") {
      return <Chip icon={<CheckCircleIcon />} label="Traité" color="success" />;
    }
    if (invoice.status === "warning") {
      return <Chip icon={<WarningIcon />} label="Avertissement" color="warning" />;
    }
    return <Chip icon={<ErrorIcon />} label="Échec" color="error" />;
  };

  return (
    <Box
      sx={{
        minHeight: "calc(100vh - 64px)",
        backgroundColor: "background.default",
        py: 4,
      }}
    >
      <Container maxWidth="md">
        <Button
          component={Link}
          href="/historique"
          startIcon={<ArrowBackIcon />}
          sx={{ mb: 2 }}
        >
          Retour
        </Button>

        <Paper sx={{ p: 4 }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 2,
            }}
          >
            <Typography variant="h5">Facture #{invoice.id}</Typography>
            {statusBadge()}
          </Box>

          <Typography variant="body2" color="text.secondary" gutterBottom>
            Fichier : {invoice.filename}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Importée le :{" "}
            {invoice.created_at
              ? new Date(invoice.created_at).toLocaleString("fr-FR")
              : "—"}
          </Typography>

          <Divider sx={{ my: 3 }} />

          {/* Classification */}
          <Typography
            variant="subtitle1"
            color="secondary.main"
            gutterBottom
            sx={{ fontWeight: "bold" }}
          >
            Classification
          </Typography>

          <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 3 }}>
            <Chip
              label={
                LABEL_FR[invoice.classification.label] ||
                invoice.classification.label
              }
              color="primary"
            />
            <Typography variant="body2" color="text.secondary">
              Confiance : {(invoice.classification.confidence * 100).toFixed(1)}%
            </Typography>
          </Box>

          {/* Données extraites — MODE ÉDITION */}
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 1,
            }}
          >
            <Typography
              variant="subtitle1"
              color="secondary.main"
              sx={{ fontWeight: "bold" }}
            >
              Données extraites
            </Typography>
            {!editMode ? (
              <Button
                size="small"
                variant="outlined"
                startIcon={<EditIcon />}
                onClick={handleEdit}
              >
                Modifier
              </Button>
            ) : (
              <Box sx={{ display: "flex", gap: 1 }}>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<CancelIcon />}
                  onClick={handleCancel}
                  disabled={saving}
                >
                  Annuler
                </Button>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />}
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? "Sauvegarde..." : "Sauvegarder"}
                </Button>
              </Box>
            )}
          </Box>

          {!editMode ? (
            // Mode lecture
            <Table size="small" sx={{ mb: 3 }}>
              <TableBody>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold", width: "40%" }}>
                    Fournisseur
                  </TableCell>
                  <TableCell>{invoice.extracted.supplier || "—"}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>N° facture</TableCell>
                  <TableCell>{invoice.extracted.invoice_number || "—"}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>Date</TableCell>
                  <TableCell>{invoice.extracted.date || "—"}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>Montant HT</TableCell>
                  <TableCell>
                    {invoice.extracted.total_ht !== null
                      ? `${invoice.extracted.total_ht.toFixed(2)} MAD`
                      : "—"}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>TVA</TableCell>
                  <TableCell>
                    {invoice.extracted.vat !== null
                      ? `${invoice.extracted.vat.toFixed(2)} MAD`
                      : "—"}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>Montant TTC</TableCell>
                  <TableCell>
                    {invoice.extracted.total_ttc !== null
                      ? `${invoice.extracted.total_ttc.toFixed(2)} MAD`
                      : "—"}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          ) : (
            // Mode édition
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 3 }}>
              <TextField
                label="Fournisseur"
                value={form.supplier}
                onChange={(e) => setForm({ ...form, supplier: e.target.value })}
                size="small"
                fullWidth
              />
              <TextField
                label="N° facture"
                value={form.invoice_number}
                onChange={(e) => setForm({ ...form, invoice_number: e.target.value })}
                size="small"
                fullWidth
              />
              <TextField
                label="Date (YYYY-MM-DD)"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                size="small"
                fullWidth
                placeholder="2024-10-11"
                error={!!form.date && !/^\d{4}-\d{2}-\d{2}$/.test(form.date)}
                helperText={
                  form.date && !/^\d{4}-\d{2}-\d{2}$/.test(form.date)
                    ? "Format attendu : YYYY-MM-DD"
                    : ""
                }
              />
              <TextField
                label="Montant HT (MAD)"
                value={form.total_ht}
                onChange={(e) => setForm({ ...form, total_ht: e.target.value })}
                size="small"
                fullWidth
                type="number"
                slotProps={{ htmlInput: { step: "0.01", min: "0" } }}
              />
              <TextField
                label="TVA (MAD)"
                value={form.vat}
                onChange={(e) => setForm({ ...form, vat: e.target.value })}
                size="small"
                fullWidth
                type="number"
                slotProps={{ htmlInput: { step: "0.01", min: "0" } }}
              />
              <TextField
                label="Montant TTC (MAD)"
                value={form.total_ttc}
                onChange={(e) => setForm({ ...form, total_ttc: e.target.value })}
                size="small"
                fullWidth
                type="number"
                slotProps={{ htmlInput: { step: "0.01", min: "0" } }}
              />

              {/* Aperçu cohérence HT + TVA = TTC */}
              {form.total_ht && form.vat && form.total_ttc && (
                <Alert
                  severity={
                    Math.abs(
                      parseFloat(form.total_ht) + parseFloat(form.vat) - parseFloat(form.total_ttc)
                    ) < 0.01
                      ? "success"
                      : "warning"
                  }
                  sx={{ py: 0.5 }}
                >
                  <Typography variant="caption">
                    Vérification : HT + TVA ={" "}
                    {(parseFloat(form.total_ht) + parseFloat(form.vat)).toFixed(2)} MAD
                    {Math.abs(
                      parseFloat(form.total_ht) + parseFloat(form.vat) - parseFloat(form.total_ttc)
                    ) < 0.01
                      ? " ✓ Cohérent avec TTC"
                      : ` ≠ TTC (${parseFloat(form.total_ttc).toFixed(2)} MAD)`}
                  </Typography>
                </Alert>
              )}
            </Box>
          )}

          {/* Warnings */}
          {invoice.validation.warnings.length > 0 && (
            <>
              <Typography
                variant="subtitle1"
                color="secondary.main"
                gutterBottom
                sx={{ fontWeight: "bold" }}
              >
                Avertissements
              </Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 3 }}>
                {invoice.validation.warnings.map((w) => (
                  <Chip
                    key={w}
                    label={WARNING_FR[w] || w}
                    color="warning"
                    variant="outlined"
                    size="small"
                  />
                ))}
              </Box>
            </>
          )}

          <Divider sx={{ my: 3 }} />

          {/* Actions */}
          <Box sx={{ display: "flex", gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={() => downloadInvoice(invoice.id)}
            >
              Télécharger JSON
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleDelete}
            >
              Supprimer
            </Button>
          </Box>
        </Paper>
      </Container>

      {/* Snackbar de succès */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={4000}
        onClose={() => setSuccessMessage(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity="success"
          onClose={() => setSuccessMessage(null)}
          sx={{ width: "100%" }}
        >
          <AlertTitle>Succès</AlertTitle>
          {successMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
}
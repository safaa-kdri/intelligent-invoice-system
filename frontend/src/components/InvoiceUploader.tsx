"use client";

import { useState, useRef } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
  AlertTitle,
  CircularProgress,
  Chip,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Stack,
  LinearProgress,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningIcon from "@mui/icons-material/Warning";
import ErrorIcon from "@mui/icons-material/Error";
import DescriptionIcon from "@mui/icons-material/Description";
import {
  uploadInvoice,
  InvoiceResponse,
  ApiError,
} from "@/lib/api";

const ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png"];
const MAX_SIZE_MB = 10;

// Traduction des labels de classification
const LABEL_FR: Record<string, string> = {
  facture_achat: "Facture d'achat",
  facture_vente: "Facture de vente",
  autre: "Autre document",
};

// Traduction des warnings
const WARNING_FR: Record<string, string> = {
  PIPELINE_IA_NOT_CONNECTED: "Pipeline IA pas encore connecté",
  BLURRY_IMAGE: "Image floue",
  DARK_IMAGE: "Image trop sombre",
  SKEWED_IMAGE: "Image inclinée",
  BAD_FRAMING: "Cadrage incorrect",
  AMOUNT_MISMATCH: "HT + TVA ≠ TTC",
  INVALID_DATE: "Date invalide",
  POTENTIAL_DUPLICATE: "Doublon potentiel",
  LOW_CONFIDENCE: "Confiance faible",
};

export default function InvoiceUploader() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InvoiceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Validation côté client avant envoi
  const validateFile = (f: File): string | null => {
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Format non supporté (${ext}). Utilisez PDF, JPG, JPEG ou PNG.`;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      return `Fichier trop volumineux (${(f.size / 1024 / 1024).toFixed(
        2
      )} Mo). Maximum : ${MAX_SIZE_MB} Mo.`;
    }
    if (f.size === 0) {
      return "Le fichier est vide (0 octet).";
    }
    return null;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    setError(null);
    setResult(null);

    if (!f) {
      setFile(null);
      return;
    }

    const validationError = validateFile(f);
    if (validationError) {
      setError(validationError);
      setFile(null);
      return;
    }

    setFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(0);

    // Fausse barre de progression (le vrai upload est rapide, c'est l'IA qui prend du temps)
    const progressInterval = setInterval(() => {
      setProgress((prev) => Math.min(prev + 10, 90));
    }, 300);

    try {
      const response = await uploadInvoice(file);
      setProgress(100);
      setResult(response);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: ApiError } };
      const apiError = axiosError.response?.data;
      setError(
        apiError?.error?.message ||
          "Erreur de communication avec le serveur. Vérifiez que Flask tourne sur le port 5000."
      );
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
      setTimeout(() => setProgress(0), 1000);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setProgress(0);
    if (inputRef.current) inputRef.current.value = "";
  };

  const renderQuality = (q: InvoiceResponse["quality"]) => {
    const items: { label: string; ok: boolean }[] = [
      { label: "Netteté", ok: !q.is_blurry },
      { label: "Luminosité", ok: !q.is_dark },
      { label: "Orientation", ok: !q.is_skewed },
      { label: "Cadrage", ok: !q.is_badly_framed },
    ];
    return (
      <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }} useFlexGap>
        {items.map((item) => (
          <Chip
            key={item.label}
            label={`${item.label} ${item.ok ? "OK" : "KO"}`}
            color={item.ok ? "success" : "warning"}
            size="small"
            variant={item.ok ? "outlined" : "filled"}
          />
        ))}
      </Stack>
    );
  };

  const renderStatusBadge = (status: InvoiceResponse["status"]) => {
    if (status === "processed") {
      return (
        <Chip
          icon={<CheckCircleIcon />}
          label="Traité avec succès"
          color="success"
        />
      );
    }
    if (status === "warning") {
      return (
        <Chip
          icon={<WarningIcon />}
          label="Traité avec avertissements"
          color="warning"
        />
      );
    }
    return (
      <Chip icon={<ErrorIcon />} label="Échec du traitement" color="error" />
    );
  };

  return (
    <Box>
      {/* ===== ZONE D'UPLOAD ===== */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            sx={{
              border: "2px dashed",
              borderColor: file ? "primary.main" : "grey.400",
              borderRadius: 2,
              p: 4,
              textAlign: "center",
              backgroundColor: file ? "primary.50" : "background.default",
              transition: "all 0.2s",
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept={ALLOWED_EXTENSIONS.join(",")}
              onChange={handleFileChange}
              style={{ display: "none" }}
              id="file-input"
            />
            <label htmlFor="file-input">
              <Button
                variant="outlined"
                component="span"
                startIcon={<CloudUploadIcon />}
                sx={{ mb: 2 }}
              >
                Sélectionner un fichier
              </Button>
            </label>
            <Typography variant="body2" color="text.secondary">
              Formats acceptés : PDF, JPG, JPEG, PNG — Max {MAX_SIZE_MB} Mo
            </Typography>
            {file && (
              <Box sx={{ mt: 2 }}>
                <Chip
                  icon={<DescriptionIcon />}
                  label={`${file.name} (${(file.size / 1024).toFixed(0)} Ko)`}
                  color="primary"
                  variant="outlined"
                />
              </Box>
            )}
          </Box>

          {/* ✅ CORRECTION 1 : justifyContent déplacé dans sx */}
          <Stack
            direction="row"
            spacing={2}
            sx={{ mt: 3, justifyContent: "center" }}
          >
            <Button
              variant="contained"
              size="large"
              onClick={handleUpload}
              disabled={!file || loading}
              startIcon={
                loading ? (
                  <CircularProgress size={20} color="inherit" />
                ) : (
                  <CloudUploadIcon />
                )
              }
            >
              {loading ? "Traitement en cours..." : "Analyser la facture"}
            </Button>
            {(file || result || error) && !loading && (
              <Button variant="outlined" onClick={handleReset}>
                Réinitialiser
              </Button>
            )}
          </Stack>

          {loading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress variant="determinate" value={progress} />
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ mt: 1, display: "block", textAlign: "center" }}
              >
                Analyse en cours... {progress}%
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* ===== ERREUR ===== */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          <AlertTitle>Erreur</AlertTitle>
          {error}
        </Alert>
      )}

      {/* ===== RÉSULTAT ===== */}
      {result && (
        <Card>
          <CardContent>
            {/* ✅ CORRECTION 2 : justifyContent + alignItems + mb dans sx */}
            <Stack
              direction="row"
              sx={{
                justifyContent: "space-between",
                alignItems: "center",
                mb: 2,
              }}
            >
              <Typography variant="h6">Résultat de l&apos;analyse</Typography>
              {renderStatusBadge(result.status)}
            </Stack>

            <Divider sx={{ mb: 2 }} />

            {/* Classification */}
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: "bold", color: "secondary.main" }}
              gutterBottom
            >
              Classification
            </Typography>

            {/* ✅ CORRECTION 3 : alignItems + mb dans sx */}
            <Stack
              direction="row"
              spacing={2}
              sx={{ alignItems: "center", mb: 2 }}
            >
              <Chip
                label={
                  LABEL_FR[result.classification.label] ||
                  result.classification.label
                }
                color="primary"
                size="medium"
              />
              <Typography variant="body2" color="text.secondary">
                Confiance : {(result.classification.confidence * 100).toFixed(1)}%
              </Typography>
            </Stack>

            {/* Qualité */}
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: "bold", color: "secondary.main" }}
              gutterBottom
            >
              Contrôle qualité
            </Typography>
            <Box sx={{ mb: 2 }}>{renderQuality(result.quality)}</Box>

            {/* Données extraites */}
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: "bold", color: "secondary.main" }}
              gutterBottom
            >
              Données extraites
            </Typography>
            <Table size="small" sx={{ mb: 2 }}>
              <TableBody>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold", width: "40%" }}>
                    Fournisseur
                  </TableCell>
                  <TableCell>{result.extracted.supplier || "—"}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>
                    N° facture
                  </TableCell>
                  <TableCell>
                    {result.extracted.invoice_number || "—"}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>Date</TableCell>
                  <TableCell>{result.extracted.date || "—"}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>
                    Montant HT
                  </TableCell>
                  <TableCell>
                    {result.extracted.total_ht !== null
                      ? `${result.extracted.total_ht.toFixed(2)} MAD`
                      : "—"}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>TVA</TableCell>
                  <TableCell>
                    {result.extracted.vat !== null
                      ? `${result.extracted.vat.toFixed(2)} MAD`
                      : "—"}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: "bold" }}>
                    Montant TTC
                  </TableCell>
                  <TableCell>
                    {result.extracted.total_ttc !== null
                      ? `${result.extracted.total_ttc.toFixed(2)} MAD`
                      : "—"}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>

            {/* Warnings */}
            {result.validation.warnings.length > 0 && (
              <>
                <Typography
                  variant="subtitle1"
                  sx={{ fontWeight: "bold", color: "secondary.main" }}
                  gutterBottom
                >
                  Avertissements
                </Typography>
                <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }} useFlexGap>
                  {result.validation.warnings.map((w) => (
                    <Chip
                      key={w}
                      label={WARNING_FR[w] || w}
                      color="warning"
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Stack>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
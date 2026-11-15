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
  Divider,
  Table,
  TableBody,
  TableRow,
  TableCell,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteIcon from "@mui/icons-material/Delete";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningIcon from "@mui/icons-material/Warning";
import ErrorIcon from "@mui/icons-material/Error";
import {
  getInvoiceById,
  deleteInvoice,
  downloadInvoice,
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
  SKEWED_IMAGE: "Image inclinée",
  BAD_FRAMING: "Cadrage incorrect",
  AMOUNT_MISMATCH: "HT + TVA ≠ TTC",
  INVALID_DATE: "Date invalide",
  POTENTIAL_DUPLICATE: "Doublon potentiel",
  LOW_CONFIDENCE: "Confiance faible",
};

export default function InvoiceDetailContent() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [invoice, setInvoice] = useState<InvoiceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInvoice = async () => {
      setLoading(true);
      try {
        const data = await getInvoiceById(id);
        setInvoice(data);
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
    if (!confirm(`Supprimer la facture #${id} ?`)) return;
    try {
      await deleteInvoice(id);
      router.push("/historique");
    } catch {
      alert("Erreur lors de la suppression.");
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
      return (
        <Chip icon={<CheckCircleIcon />} label="Traité" color="success" />
      );
    }
    if (invoice.status === "warning") {
      return (
        <Chip
          icon={<WarningIcon />}
          label="Avertissement"
          color="warning"
        />
      );
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

          <Typography
            variant="subtitle1"
            color="secondary.main"
            gutterBottom
            sx={{ fontWeight: "bold" }}
          >
            Classification
          </Typography>

          <Box
            sx={{
              display: "flex",
              gap: 2,
              alignItems: "center",
              mb: 3,
            }}
          >
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

          <Typography
            variant="subtitle1"
            color="secondary.main"
            gutterBottom
            sx={{ fontWeight: "bold" }}
          >
            Données extraites
          </Typography>
          <Table size="small" sx={{ mb: 3 }}>
            <TableBody>
              <TableRow>
                <TableCell sx={{ fontWeight: "bold", width: "40%" }}>
                  Fournisseur
                </TableCell>
                <TableCell>{invoice.extracted.supplier || "—"}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ fontWeight: "bold" }}>
                  N° facture
                </TableCell>
                <TableCell>
                  {invoice.extracted.invoice_number || "—"}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ fontWeight: "bold" }}>Date</TableCell>
                <TableCell>{invoice.extracted.date || "—"}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ fontWeight: "bold" }}>
                  Montant HT
                </TableCell>
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
                <TableCell sx={{ fontWeight: "bold" }}>
                  Montant TTC
                </TableCell>
                <TableCell>
                  {invoice.extracted.total_ttc !== null
                    ? `${invoice.extracted.total_ttc.toFixed(2)} MAD`
                    : "—"}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>

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

              <Box
                sx={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 1,
                  mb: 3,
                }}
              >
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
    </Box>
  );
}
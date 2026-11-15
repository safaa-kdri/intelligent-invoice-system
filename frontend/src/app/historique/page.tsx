"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Box,
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Tooltip,
  TextField,
  MenuItem,
} from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import DeleteIcon from "@mui/icons-material/Delete";
import DownloadIcon from "@mui/icons-material/Download";
import {
  getInvoices,
  deleteInvoice,
  downloadInvoice,
  InvoiceListResponse,
} from "@/lib/api";

const LABEL_FR: Record<string, string> = {
  facture_achat: "Facture d'achat",
  facture_vente: "Facture de vente",
  autre: "Autre document",
};

const STATUS_FR: Record<
  string,
  { label: string; color: "success" | "warning" | "error" | "default" }
> = {
  processed: { label: "Traité", color: "success" },
  warning: { label: "Avertissement", color: "warning" },
  failed: { label: "Échec", color: "error" },
  pending: { label: "En cours", color: "default" },
};

export default function HistoriquePage() {
  const [data, setData] = useState<InvoiceListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [labelFilter, setLabelFilter] = useState<string>("");
  const [refreshKey, setRefreshKey] = useState(0);

  // ✅ Correction : déplacer setState dans le .then() pour éviter l'avertissement
  useEffect(() => {
    let ignore = false;

    async function fetchData() {
      try {
        const response = await getInvoices({
          page: page + 1,
          limit: rowsPerPage,
          status: statusFilter
            ? (statusFilter as "processed" | "warning" | "failed")
            : undefined,
          label: labelFilter
            ? (labelFilter as "facture_achat" | "facture_vente" | "autre")
            : undefined,
        });

        if (!ignore) {
          setData(response);
          setError(null);
          setLoading(false);
        }
      } catch {
        if (!ignore) {
          setError(
            "Impossible de charger l'historique. Vérifiez que Flask tourne sur le port 5000."
          );
          setLoading(false);
        }
      }
    }

    // Marquer en chargement AVANT la requête (mais pas de setState synchrone)
    // On utilise un setTimeout pour sortir du cycle synchrone de l'effet
    const timer = setTimeout(() => {
      if (!ignore) setLoading(true);
      fetchData();
    }, 0);

    return () => {
      ignore = true;
      clearTimeout(timer);
    };
  }, [page, rowsPerPage, statusFilter, labelFilter, refreshKey]);

  const handleDelete = async (id: number) => {
    if (
      !confirm(
        `Supprimer la facture #${id} ? Cette action est irréversible.`
      )
    ) {
      return;
    }
    try {
      await deleteInvoice(id);
      // ✅ Recharger via refreshKey au lieu d'appeler fetchInvoices()
      setRefreshKey((prev) => prev + 1);
    } catch {
      alert("Erreur lors de la suppression.");
    }
  };

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString("fr-FR");
    } catch {
      return iso;
    }
  };

  return (
    <Box
      sx={{
        minHeight: "calc(100vh - 64px)",
        backgroundColor: "background.default",
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        <Typography
          variant="h4"
          gutterBottom
          sx={{ mb: 3, fontWeight: 600, color: "secondary.main" }}
        >
          Historique des factures
        </Typography>

        {/* Filtres */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box
            sx={{
              display: "flex",
              flexDirection: { xs: "column", sm: "row" },
              gap: 2,
            }}
          >
            <TextField
              select
              label="Statut"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(0);
              }}
              size="small"
              sx={{ minWidth: 180 }}
            >
              <MenuItem value="">Tous</MenuItem>
              <MenuItem value="processed">Traité</MenuItem>
              <MenuItem value="warning">Avertissement</MenuItem>
              <MenuItem value="failed">Échec</MenuItem>
            </TextField>

            <TextField
              select
              label="Type de document"
              value={labelFilter}
              onChange={(e) => {
                setLabelFilter(e.target.value);
                setPage(0);
              }}
              size="small"
              sx={{ minWidth: 200 }}
            >
              <MenuItem value="">Tous</MenuItem>
              <MenuItem value="facture_achat">Facture d&apos;achat</MenuItem>
              <MenuItem value="facture_vente">Facture de vente</MenuItem>
              <MenuItem value="autre">Autre document</MenuItem>
            </TextField>
          </Box>
        </Paper>

        {/* Erreur */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Tableau */}
        <Paper>
          {loading ? (
            <Box sx={{ display: "flex", justifyContent: "center", p: 6 }}>
              <CircularProgress />
            </Box>
          ) : !data || data.invoices.length === 0 ? (
            <Box sx={{ p: 6, textAlign: "center" }}>
              <Typography color="text.secondary">
                Aucune facture trouvée.
              </Typography>
            </Box>
          ) : (
            <>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ backgroundColor: "grey.100" }}>
                      <TableCell sx={{ fontWeight: "bold" }}>ID</TableCell>
                      <TableCell sx={{ fontWeight: "bold" }}>Fichier</TableCell>
                      <TableCell sx={{ fontWeight: "bold" }}>Type</TableCell>
                      <TableCell sx={{ fontWeight: "bold" }}>Statut</TableCell>
                      <TableCell sx={{ fontWeight: "bold" }}>Date</TableCell>
                      <TableCell sx={{ fontWeight: "bold" }} align="right">
                        Actions
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.invoices.map((row) => (
                      <TableRow key={row.id} hover>
                        <TableCell>{row.id}</TableCell>
                        <TableCell
                          sx={{
                            maxWidth: 200,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {row.nom_fichier}
                        </TableCell>
                        <TableCell>
                          {row.type_document ? (
                            <Chip
                              label={
                                LABEL_FR[row.type_document] || row.type_document
                              }
                              size="small"
                              color="primary"
                              variant="outlined"
                            />
                          ) : (
                            "—"
                          )}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={
                              STATUS_FR[row.statut]?.label || row.statut
                            }
                            size="small"
                            color={STATUS_FR[row.statut]?.color || "default"}
                          />
                        </TableCell>
                        <TableCell>
                          {formatDate(row.date_importation)}
                        </TableCell>
                        <TableCell align="right">
                          <Tooltip title="Voir le détail">
                            <IconButton
                              component={Link}
                              href={`/invoices/${row.id}`}
                              color="primary"
                              size="small"
                            >
                              <VisibilityIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Télécharger JSON">
                            <IconButton
                              onClick={() => downloadInvoice(row.id)}
                              color="info"
                              size="small"
                            >
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Supprimer">
                            <IconButton
                              onClick={() => handleDelete(row.id)}
                              color="error"
                              size="small"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                component="div"
                count={data.total}
                page={page}
                onPageChange={handleChangePage}
                rowsPerPage={rowsPerPage}
                onRowsPerPageChange={handleChangeRowsPerPage}
                rowsPerPageOptions={[5, 10, 20, 50]}
                labelRowsPerPage="Lignes par page"
                labelDisplayedRows={({ from, to, count }) =>
                  `${from}-${to} sur ${count !== -1 ? count : `plus de ${to}`}`
                }
              />
            </>
          )}
        </Paper>
      </Container>
    </Box>
  );
}
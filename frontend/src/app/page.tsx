import { Box, Container, Typography, Paper } from "@mui/material";
import InvoiceUploader from "@/components/InvoiceUploader";

export default function Home() {
  return (
    <Box
      sx={{
        minHeight: "calc(100vh - 64px)",
        backgroundColor: "background.default",
        py: 6,
      }}
    >
      <Container maxWidth="md">
        <Paper
          elevation={0}
          sx={{
            p: 4,
            mb: 4,
            backgroundColor: "secondary.main",
            color: "white",
            borderRadius: 2,
          }}
        >
          <Typography variant="h4" component="h1" sx={{ color: "white", mb: 1 }}>
            Importer une facture
          </Typography>
          <Typography variant="body1" sx={{ opacity: 0.9 }}>
            Importez une facture (PDF, JPG ou PNG) pour l&apos;analyser automatiquement :
            classification, contrôle qualité et extraction des informations.
          </Typography>
        </Paper>

        <InvoiceUploader />

        <Box sx={{ textAlign: "center", mt: 6, color: "text.secondary" }}>
          <Typography variant="caption">
            EMSI — Projet 2026-2027 — El Kadouri Safaa &amp; Nahal Aya
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}
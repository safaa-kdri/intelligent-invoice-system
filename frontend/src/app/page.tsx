"use client";

import { Box, Typography, Grid, Card, Button, LinearProgress } from "@mui/material";
import Link from "next/link";
import { ArrowRight, FileText, CheckCircle, AlertCircle } from "lucide-react";

export default function Dashboard() {
  return (
    <Box sx={{ maxWidth: 1200, mx: "auto", px: { xs: 2, md: 4 }, pt: { xs: 8, md: 4 } }}>
      
      {/* En-tête Éditorial */}
      <Box sx={{ mb: 10, display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: 4 }}>
        <Box>
          <Typography variant="overline" color="primary.main" gutterBottom sx={{ display: "block", letterSpacing: "0.15em" }}>
            TABLEAU DE BORD
          </Typography>
          <Typography variant="h1" sx={{ mb: 2, fontSize: { xs: "2.5rem", md: "4rem" } }}>
            Bonjour,<br />votre activité en un coup d'œil.
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 500 }}>
            Suivez l'évolution de vos factures traitées par notre intelligence artificielle.
          </Typography>
        </Box>
        <Button component={Link} href="/upload" variant="contained" color="primary" size="large" endIcon={<ArrowRight size={18} />}>
          Nouvelle analyse
        </Button>
      </Box>

      {/* Cartes de Statistiques (KPIs) */}
      <Grid container spacing={3} sx={{ mb: 8 }}>
        {[
          { label: "Factures traitées", value: "1,248", trend: "+12% ce mois", icon: <FileText size={24} />, color: "#0F4C3F" },
          { label: "Taux de succès", value: "98,5 %", trend: "Qualité excellente", icon: <CheckCircle size={24} />, color: "#2E7D32" },
          { label: "Anomalies détectées", value: "42", trend: "À vérifier", icon: <AlertCircle size={24} />, color: "#ED6C02" },
        ].map((stat, i) => (
          <Grid size={{ xs: 12, md: 4 }} key={i}>
            <Card sx={{ p: 4, height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 4 }}>
                <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: `${stat.color}15`, color: stat.color }}>
                  {stat.icon}
                </Box>
              </Box>
              <Box>
                <Typography variant="h3" sx={{ fontFamily: "var(--font-playfair)", fontWeight: 600, mb: 1 }}>
                  {stat.value}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {stat.label}
                </Typography>
                <Typography variant="caption" sx={{ color: stat.color, fontWeight: 500 }}>
                  {stat.trend}
                </Typography>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Section Activité Récente (Design Éditorial) */}
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "2fr 1fr" }, gap: 4 }}>
        <Card sx={{ p: 4 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 4 }}>
            <Typography variant="h6" sx={{ fontFamily: "var(--font-playfair)", fontSize: "1.5rem" }}>
              Derniers documents
            </Typography>
            <Button component={Link} href="/historique" size="small" sx={{ color: "primary.main" }}>
              Tout voir
            </Button>
          </Box>
          {[1, 2, 3].map((item) => (
            <Box key={item} sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", py: 2, borderBottom: "1px solid", borderColor: "divider" }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Box sx={{ width: 40, height: 40, borderRadius: 1, bgcolor: "action.hover", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <FileText size={20} color="#6E726F" />
                </Box>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>Facture_F2026_{item}.pdf</Typography>
                  <Typography variant="caption" color="text.secondary">Il y a 2 heures</Typography>
                </Box>
              </Box>
              <Typography variant="body2" sx={{ fontFamily: "var(--font-plex-mono)", fontWeight: 500 }}>
                1 250,00 MAD
              </Typography>
            </Box>
          ))}
        </Card>

        <Card sx={{ p: 4, bgcolor: "primary.main", color: "primary.contrastText" }}>
          <Typography variant="h6" sx={{ fontFamily: "var(--font-playfair)", fontSize: "1.5rem", mb: 2 }}>
            Santé du système
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.8, mb: 4 }}>
            Tous les modules d'intelligence artificielle fonctionnent de manière optimale.
          </Typography>
          <Box sx={{ mb: 1, display: "flex", justifyContent: "space-between" }}>
            <Typography variant="caption">Précision OCR</Typography>
            <Typography variant="caption" sx={{ fontWeight: 600 }}>99%</Typography>
          </Box>
          <LinearProgress variant="determinate" value={99} sx={{ height: 6, borderRadius: 3, bgcolor: "rgba(255,255,255,0.2)", "& .MuiLinearProgress-bar": { bgcolor: "primary.contrastText" } }} />
        </Card>
      </Box>
    </Box>
  );
}
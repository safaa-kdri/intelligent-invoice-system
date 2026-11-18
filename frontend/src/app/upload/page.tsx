"use client";

import { useRouter } from "next/navigation";
import { Box, Typography, Button, Card, Stack, IconButton, Container, CircularProgress } from "@mui/material";
import { UploadCloud, FileText, X, CheckCircle2 } from "lucide-react";
import { useState, useCallback } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";
import { uploadInvoice } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalyze = async () => {
    if (!file || isAnalyzing) return;

    setError(null);
    setIsAnalyzing(true);

    try {
      const invoice = await uploadInvoice(file);
      router.push(`/invoices/${invoice.id}`);
    } catch (uploadError: unknown) {
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : "Une erreur inattendue est survenue pendant l'analyse."
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const onDrop = useCallback((acceptedFiles: File[], fileRejections: FileRejection[]) => {
    setError(null);
    if (fileRejections.length > 0) {
      const rejection = fileRejections[0];
      if (rejection.errors[0].code === "file-too-large") setError("Le fichier dépasse la limite de 10 Mo.");
      else if (rejection.errors[0].code === "file-invalid-type") setError("Format non supporté. Utilisez PDF, JPG ou PNG.");
      return;
    }
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      if (acceptedFiles[0].type.startsWith("image/")) {
        setPreview(URL.createObjectURL(acceptedFiles[0]));
      } else {
        setPreview(null);
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "image/jpeg": [".jpg", ".jpeg"], "image/png": [".png"] },
    maxSize: 10 * 1024 * 1024,
    maxFiles: 1,
  });

  // On extrait les props pour les attacher au div natif
  const rootProps = getRootProps();

  return (
    <Container maxWidth="md" sx={{ pt: { xs: 12, md: 10 }, pb: 8 }}>
      <Box sx={{ textAlign: "center", mb: 8 }}>
        <Typography variant="overline" color="primary.main" gutterBottom sx={{ display: "block", letterSpacing: "0.2em", fontWeight: 600 }}>
          NOUVELLE ANALYSE
        </Typography>
        <Typography variant="h1" sx={{ mb: 3, fontSize: { xs: "2.5rem", md: "4rem" }, lineHeight: 1.1 }}>
          Déposez votre <br /> facture.
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 500, mx: "auto", fontSize: "1.1rem" }}>
          Notre intelligence artificielle extrait et vérifie automatiquement les données de vos documents.
        </Typography>
      </Box>

      {!file ? (
        <div {...rootProps} style={{ cursor: "pointer" }}>
          <input {...getInputProps()} />
          <Box
            sx={{
              position: "relative",
              overflow: "hidden",
              border: "1px solid",
              borderColor: isDragActive ? "primary.main" : "rgba(20, 24, 27, 0.1)",
              bgcolor: isDragActive ? "rgba(15, 76, 63, 0.03)" : "background.paper",
              borderRadius: 4,
              p: { xs: 6, md: 10 },
              textAlign: "center",
              transition: "all 0.4s ease",
              boxShadow: isDragActive ? "0 20px 40px rgba(15, 76, 63, 0.08)" : "0 10px 30px rgba(0,0,0,0.02)",
              "&:hover": {
                borderColor: "primary.main",
                bgcolor: "rgba(15, 76, 63, 0.01)",
                boxShadow: "0 20px 40px rgba(0,0,0,0.04)",
                "& .scan-line": { transform: "translateY(200px)", opacity: 1 }
              },
            }}
          >
            <Box className="scan-line" sx={{ position: "absolute", top: 0, left: 0, right: 0, height: "2px", background: "linear-gradient(90deg, transparent, #0F4C3F, transparent)", opacity: 0, transition: "all 0.7s ease-in-out", zIndex: 1 }} />

            <Box sx={{ width: 80, height: 80, borderRadius: "50%", bgcolor: "rgba(15, 76, 63, 0.06)", display: "flex", alignItems: "center", justifyContent: "center", mx: "auto", mb: 4, color: "primary.main" }}>
              <UploadCloud size={40} strokeWidth={1.5} />
            </Box>
            <Typography variant="h4" sx={{ fontFamily: "var(--font-playfair)", mb: 2 }}>
              {isDragActive ? "Relâchez pour déposer" : "Glissez-déposez ici"}
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
              ou cliquez pour parcourir vos fichiers
            </Typography>

            <Stack direction="row" spacing={2} sx={{ justifyContent: "center", alignItems: "center", color: "text.secondary", fontSize: "0.85rem" }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}><CheckCircle2 size={14} /> PDF, JPG, PNG</Box>
              <Typography>•</Typography>
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}><CheckCircle2 size={14} /> Max 10 Mo</Box>
            </Stack>
          </Box>
        </div>
      ) : (
        <Card sx={{ p: { xs: 3, md: 6 }, boxShadow: "0 20px 40px rgba(0,0,0,0.04)" }}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={4} sx={{ alignItems: "center" }}>
            <Box sx={{ width: 180, height: 220, bgcolor: "action.hover", borderRadius: 2, display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden", border: "1px solid", borderColor: "divider" }}>
              {preview ? <img src={preview} alt="Aperçu" style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : <FileText size={64} color="#6E726F" strokeWidth={1} />}
            </Box>
            <Box sx={{ flex: 1, textAlign: { xs: "center", sm: "left" } }}>
              <Typography variant="overline" color="primary.main" gutterBottom sx={{ display: "block", letterSpacing: "0.1em" }}>
                FICHIER PRÊT
              </Typography>
              <Typography variant="h5" sx={{ fontFamily: "var(--font-playfair)", mb: 1, wordBreak: "break-all" }}>{file.name}</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 4, fontFamily: "var(--font-plex-mono)" }}>{(file.size / 1024 / 1024).toFixed(2)} Mo</Typography>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                startIcon={isAnalyzing ? <CircularProgress size={18} color="inherit" /> : undefined}
                sx={{ width: { xs: "100%", sm: "auto" }, px: 4, py: 1.5 }}
              >
                {isAnalyzing ? "Analyse en cours..." : "Lancer l'analyse"}
              </Button>
            </Box>
            <IconButton disabled={isAnalyzing} onClick={() => { setFile(null); setPreview(null); setError(null); }} sx={{ color: "error.main", alignSelf: { xs: "center", sm: "flex-start" } }}>
              <X size={24} />
            </IconButton>
          </Stack>
        </Card>
      )}
      {error && <Box role="alert" sx={{ mt: 4, p: 3, bgcolor: "error.main", color: "error.contrastText", borderRadius: 2, textAlign: "center" }}><Typography variant="body2" sx={{ fontWeight: 500 }}>{error}</Typography></Box>}
    </Container>
  );
}
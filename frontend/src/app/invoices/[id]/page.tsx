import { Suspense } from "react";
import { Box, CircularProgress } from "@mui/material";
import InvoiceDetailContent from "./InvoiceDetailContent";

// Server Component — pas de "use client"
// Le hook useParams() est utilisé dans InvoiceDetailContent (wrappé dans Suspense)

function LoadingFallback() {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "50vh",
      }}
    >
      <CircularProgress />
    </Box>
  );
}

export default function InvoiceDetailPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <InvoiceDetailContent />
    </Suspense>
  );
}
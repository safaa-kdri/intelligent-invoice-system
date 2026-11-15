"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import HistoryIcon from "@mui/icons-material/History";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";

function NavbarContent({ pathname }: { pathname: string | null }) {
  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname?.startsWith(href) ?? false;
  };

  return (
    <AppBar position="sticky" sx={{ backgroundColor: "secondary.main" }}>
      <Container maxWidth="lg">
        <Toolbar disableGutters>
          <ReceiptLongIcon sx={{ mr: 1.5 }} />
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, fontWeight: 600 }}
          >
            Factures IA
          </Typography>
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button
              component={Link}
              href="/"
              color="inherit"
              startIcon={<UploadFileIcon />}
              sx={{
                backgroundColor:
                  isActive("/") && pathname === "/"
                    ? "rgba(255,255,255,0.15)"
                    : "transparent",
                "&:hover": { backgroundColor: "rgba(255,255,255,0.1)" },
              }}
            >
              Importer
            </Button>
            <Button
              component={Link}
              href="/historique"
              color="inherit"
              startIcon={<HistoryIcon />}
              sx={{
                backgroundColor: isActive("/historique")
                  ? "rgba(255,255,255,0.15)"
                  : "transparent",
                "&:hover": { backgroundColor: "rgba(255,255,255,0.1)" },
              }}
            >
              Historique
            </Button>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

function NavbarWithPathname() {
  const pathname = usePathname();
  return <NavbarContent pathname={pathname} />;
}

export default function Navbar() {
  return (
    <Suspense fallback={<NavbarContent pathname={null} />}>
      <NavbarWithPathname />
    </Suspense>
  );
}
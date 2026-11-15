"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button, Box } from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import HistoryIcon from "@mui/icons-material/History";

export default function NavbarContent() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <Box sx={{ display: "flex", gap: 1 }}>
      <Button
        component={Link}
        href="/"
        color="inherit"
        startIcon={<UploadFileIcon />}
        sx={{
          backgroundColor:
            pathname === "/" ? "rgba(255,255,255,0.15)" : "transparent",
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
  );
}
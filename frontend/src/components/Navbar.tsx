"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Box, Typography } from "@mui/material";
import { LayoutDashboard, Upload, History, Layers } from "lucide-react";

function NavbarContent({ pathname }: { pathname: string | null }) {
  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname?.startsWith(href) ?? false;
  };

  const navItems = [
    { label: "Dashboard", href: "/", icon: <LayoutDashboard size={18} /> },
    { label: "Analyser", href: "/upload", icon: <Upload size={18} /> },
    { label: "Historique", href: "/historique", icon: <History size={18} /> },
  ];

  return (
    <Box sx={{ position: "fixed", top: 32, left: 0, right: 0, display: "flex", justifyContent: "center", zIndex: 1100, pointerEvents: "none" }}>
      <Box
        sx={{
          pointerEvents: "auto",
          display: "flex",
          alignItems: "center",
          gap: { xs: 1, md: 4 },
          px: { xs: 2, md: 4 },
          py: 1.5,
          borderRadius: 50,
          bgcolor: "rgba(255, 255, 255, 0.7)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(20, 24, 27, 0.04)",
          boxShadow: "0 10px 40px rgba(0,0,0,0.03)",
          ".dark &": {
            bgcolor: "rgba(18, 26, 24, 0.7)",
            borderColor: "rgba(236, 239, 234, 0.06)",
          },
        }}
      >
        {/* Logo minimaliste (juste une icône) */}
        <Box component={Link} href="/" sx={{ display: "flex", alignItems: "center", textDecoration: "none", color: "primary.main", mr: { xs: 1, md: 3 } }}>
          <Layers size={24} strokeWidth={2.5} />
        </Box>

        <Box sx={{ display: "flex", gap: 1 }}>
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Box
                key={item.href}
                component={Link}
                href={item.href}
                sx={{
                  display: "flex", alignItems: "center", gap: 1, px: 2.5, py: 1, borderRadius: 50, textDecoration: "none",
                  color: active ? "primary.main" : "text.secondary",
                  bgcolor: active ? "rgba(15, 76, 63, 0.08)" : "transparent",
                  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                  "&:hover": { 
                    bgcolor: active ? "rgba(15, 76, 63, 0.12)" : "rgba(20, 24, 27, 0.03)", 
                    color: active ? "primary.main" : "text.primary",
                    transform: "translateY(-1px)"
                  },
                }}
              >
                {item.icon}
                <Typography variant="body2" sx={{ fontWeight: active ? 600 : 500, display: { xs: "none", sm: "block" } }}>
                  {item.label}
                </Typography>
              </Box>
            );
          })}
        </Box>
      </Box>
    </Box>
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
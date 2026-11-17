"use client";

import { useState, useEffect } from "react";
import { Inter, Playfair_Display, IBM_Plex_Mono } from "next/font/google";
import { ThemeProvider as NextThemesProvider, useTheme } from "next-themes";
import { Box, CssBaseline, ThemeProvider as MuiThemeProvider } from "@mui/material";
import Navbar from "@/components/Navbar"; // On va utiliser la Navbar de Safaa qu'on va modifier
import { theme as lightTheme, darkTheme } from "@/theme/theme";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const playfair = Playfair_Display({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-playfair" });
const plexMono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-plex-mono" });

function MuiWrapper({ children }: { children: React.ReactNode }) {
  const { resolvedTheme } = useTheme();
  const muiTheme = resolvedTheme === "dark" ? darkTheme : lightTheme;
  return <MuiThemeProvider theme={muiTheme}><CssBaseline />{children}</MuiThemeProvider>;
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => setMousePos({ x: e.clientX, y: e.clientY });
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <html lang="fr" suppressHydrationWarning>
      <body className={`${inter.variable} ${playfair.variable} ${plexMono.variable}`}>
        <NextThemesProvider attribute="class" defaultTheme="system" enableSystem>
          <MuiWrapper>
            <Box sx={{ minHeight: "100vh", bgcolor: "background.default", position: "relative", overflow: "hidden" }}>
              
              {/* Lueur émeraude qui suit la souris */}
              <Box sx={{ position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh", pointerEvents: "none", zIndex: 0, background: `radial-gradient(800px circle at ${mousePos.x}px ${mousePos.y}px, rgba(15, 76, 63, 0.03), transparent 40%)` }} />
              
              <Navbar />
              
              <Box component="main" sx={{ position: "relative", zIndex: 1, pt: 12 }}>
                {children}
              </Box>
            </Box>
          </MuiWrapper>
        </NextThemesProvider>
      </body>
    </html>
  );
}
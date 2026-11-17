import { createTheme, ThemeOptions } from "@mui/material/styles";

const getDesignTokens = (mode: "light" | "dark"): ThemeOptions => {
  const isLight = mode === "light";

  return {
    palette: {
      mode,
      primary: {
        main: isLight ? "#0F4C3F" : "#5FB89A", // Vert émeraude
        contrastText: isLight ? "#F6F5F1" : "#0A0F0E",
      },
      secondary: {
        main: isLight ? "#14181B" : "#ECEFEA", // Encre / Ivoire
        contrastText: isLight ? "#F6F5F1" : "#0A0F0E",
      },
      background: {
        default: isLight ? "#F6F5F1" : "#0A0F0E", // Porcelaine / Vert-noir
        paper: isLight ? "#FFFFFF" : "#121A18",
      },
      text: {
        primary: isLight ? "#14181B" : "#ECEFEA",
        secondary: isLight ? "#6E726F" : "#8A9E98",
      },
      divider: isLight ? "rgba(20, 24, 27, 0.08)" : "rgba(236, 239, 234, 0.08)",
      success: { main: isLight ? "#2E7D32" : "#5FB89A" },
      warning: { main: isLight ? "#ED6C02" : "#D9A441" },
      error: { main: isLight ? "#D32F2F" : "#B5495B" },
    },
    typography: {
      fontFamily: "var(--font-inter), sans-serif",
      h1: { fontFamily: "var(--font-playfair), serif", fontWeight: 500, letterSpacing: "-0.02em" },
      h2: { fontFamily: "var(--font-playfair), serif", fontWeight: 500, letterSpacing: "-0.01em" },
      h3: { fontFamily: "var(--font-playfair), serif", fontWeight: 500 },
      h4: { fontFamily: "var(--font-playfair), serif", fontWeight: 500 },
      h5: { fontFamily: "var(--font-playfair), serif", fontWeight: 500 },
      h6: { fontFamily: "var(--font-playfair), serif", fontWeight: 600 },
      button: { textTransform: "none", fontWeight: 500, letterSpacing: "0.02em" },
      overline: { letterSpacing: "0.1em", fontWeight: 600, fontSize: "0.7rem" },
    },
    shape: { borderRadius: 8 }, // Coins légèrement arrondis
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: isLight ? "#F6F5F1" : "#0A0F0E",
            transition: "background-color 0.5s ease, color 0.5s ease",
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            border: `1px solid ${isLight ? "rgba(20, 24, 27, 0.06)" : "rgba(236, 239, 234, 0.06)"}`,
            boxShadow: isLight ? "0 8px 32px rgba(0,0,0,0.02)" : "0 8px 32px rgba(0,0,0,0.4)",
            backgroundImage: "none",
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 6,
            padding: "10px 24px",
            fontSize: "0.85rem",
            "&.MuiButton-containedPrimary": {
              background: `linear-gradient(135deg, ${isLight ? "#0F4C3F" : "#5FB89A"} 0%, ${isLight ? "#1F7A63" : "#8DCCB5"} 100%)`,
              border: "none",
              "&:hover": {
                background: `linear-gradient(135deg, ${isLight ? "#0A3A30" : "#4A9B80"} 0%, ${isLight ? "#16614F" : "#7AB89F"} 100%)`,
              },
            },
          },
        },
      },
    },
  };
};

export const theme = createTheme(getDesignTokens("light"));
export const darkTheme = createTheme(getDesignTokens("dark"));
"use client";

import { createTheme } from "@mui/material/styles";

// Palette alignée avec le rapport LaTeX (darkblue #1A2332, primary #148AA0)
export const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#148AA0",
      dark: "#0F6A7A",
      light: "#3BA8BD",
      contrastText: "#FFFFFF",
    },
    secondary: {
      main: "#1A2332",
      contrastText: "#FFFFFF",
    },
    background: {
      default: "#F4F6F8",
      paper: "#FFFFFF",
    },
    success: {
      main: "#2E7D32",
    },
    warning: {
      main: "#ED6C02",
    },
    error: {
      main: "#D32F2F",
    },
  },
  typography: {
    fontFamily: [
      "Roboto",
      "Helvetica",
      "Arial",
      "sans-serif",
    ].join(","),
    h4: {
      fontWeight: 600,
      color: "#1A2332",
    },
    h5: {
      fontWeight: 600,
      color: "#1A2332",
    },
    h6: {
      fontWeight: 600,
      color: "#1A2332",
    },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 600,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "0 2px 8px rgba(26, 35, 50, 0.08)",
        },
      },
    },
  },
});
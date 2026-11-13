import axios from "axios";

// URL du backend Flask (configurable via .env.local)
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

// Client axios configuré
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 secondes (l'IA peut être lente)
});

// Types conformes au contrat d'API
export interface ClassificationResult {
  label: "facture_achat" | "facture_vente" | "autre";
  confidence: number;
}

export interface QualityResult {
  is_blurry: boolean;
  is_dark: boolean;
  is_skewed: boolean;
  is_badly_framed: boolean;
  quality_status: "good" | "warning" | "bad";
  scores: {
    blur_variance: number;
    brightness_mean: number;
    skew_angle: number;
  };
}

export interface ExtractedData {
  supplier: string | null;
  invoice_number: string | null;
  date: string | null;
  total_ht: number | null;
  vat: number | null;
  total_ttc: number | null;
}

export interface ValidationResult {
  is_valid: boolean;
  warnings: string[];
}

export interface InvoiceResponse {
  id: number;
  filename: string;
  status: "processed" | "warning" | "failed";
  classification: ClassificationResult;
  quality: QualityResult;
  extracted: ExtractedData;
  validation: ValidationResult;
  ocr_text: string;
  created_at: string | null;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: string;
  };
}

// Fonction d'upload
export async function uploadInvoice(file: File): Promise<InvoiceResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post<InvoiceResponse>(
    "/api/invoices/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}

// Fonction de test (health check)
export async function checkHealth(): Promise<{ status: string }> {
  const response = await api.get("/api/health");
  return response.data;
}
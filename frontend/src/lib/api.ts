import axios from "axios";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

// ==================== TYPES ====================

export interface ClassificationResult {
  label: "facture_achat" | "facture_vente" | "autre";
  confidence: number;
  cnn_label?: "facture_achat" | "facture_vente" | "autre" | null;
  corrected?: boolean;
  correction_reason?: string | null;
  ocr_hint?: "achat" | "vente" | "indetermine";
  ocr_matches?: {
    achat: string[];
    vente: string[];
  };
}

export interface QualityResult {
  is_blurry: boolean;
  is_dark: boolean;
  is_skewed: boolean;
  is_badly_framed: boolean;
  quality_status: "good" | "warning" | "bad" | "ok";
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

export interface InvoiceListResponse {
  invoices: Array<{
    id: number;
    nom_fichier: string;
    type_document: string | null;
    statut: string;
    date_importation: string;
  }>;
  total: number;
  page: number;
  limit: number;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: string;
  };
}

export interface UpdateInvoicePayload {
  supplier?: string | null;
  invoice_number?: string | null;
  date?: string | null;
  total_ht?: number | null;
  vat?: number | null;
  total_ttc?: number | null;
}

export interface DashboardStats {
  total: number;
  processed: number;
  warnings: number;
  failed: number;
  by_type: Record<string, number>;
}

// ==================== VOS FONCTIONS (DESIGN) ====================

export function uploadInvoiceWithProgress(
  file: File,
  onProgress?: (percent: number) => void
): Promise<InvoiceResponse> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/api/invoices/upload`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as InvoiceResponse);
        } catch {
          reject(new Error("Réponse serveur invalide (JSON attendu)"));
        }
      } else {
        let msg = `Erreur ${xhr.status}`;
        try {
          const body = JSON.parse(xhr.responseText) as ApiError;
          msg = body?.error?.message ?? msg;
        } catch { /* ignore */ }
        reject(new Error(msg));
      }
    };

    xhr.onerror = () =>
      reject(new Error("Erreur réseau. Vérifiez que Flask tourne sur le port 5000."));
    xhr.ontimeout = () => reject(new Error("Délai dépassé (60 s)."));
    xhr.send(formData);
  });
}

export async function uploadInvoice(file: File): Promise<InvoiceResponse> {
  return uploadInvoiceWithProgress(file);
}

// ==================== FONCTIONS DE SAFAA (BACKEND) ====================

export async function getInvoices(params?: {
  page?: number;
  limit?: number;
  status?: "processed" | "warning" | "failed";
  label?: "facture_achat" | "facture_vente" | "autre";
}): Promise<InvoiceListResponse> {
  const response = await api.get<InvoiceListResponse>("/api/invoices", { params });
  return response.data;
}

export async function getInvoice(id: number): Promise<InvoiceResponse> {
  const response = await api.get<InvoiceResponse>(`/api/invoices/${id}`);
  return response.data;
}

export async function updateInvoice(
  id: number,
  payload: UpdateInvoicePayload
): Promise<InvoiceResponse> {
  const response = await api.put<InvoiceResponse>(`/api/invoices/${id}`, payload);
  return response.data;
}

export async function deleteInvoice(id: number): Promise<{ id: number; status: string }> {
  const response = await api.delete<{ id: number; status: string }>(`/api/invoices/${id}`);
  return response.data;
}

export function downloadInvoice(id: number): void {
  window.open(`${API_BASE_URL}/api/invoices/${id}/export`, "_blank");
}

export async function getStats(): Promise<DashboardStats> {
  const response = await api.get<DashboardStats>("/api/dashboard/stats");
  return response.data;
}

export async function checkHealth(): Promise<{ status: string }> {
  const response = await api.get("/api/health");
  return response.data;
}
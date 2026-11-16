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

// ==================== TYPES ====================

export interface InvoiceListItem {
  id: number;
  nom_fichier: string;
  type_document: string | null;
  statut: "processed" | "warning" | "failed" | "pending";
  date_importation: string;
}

export interface InvoiceListResponse {
  total: number;
  page: number;
  limit: number;
  invoices: InvoiceListItem[];
}

export interface GetInvoicesParams {
  page?: number;
  limit?: number;
  status?: "processed" | "warning" | "failed";
  label?: "facture_achat" | "facture_vente" | "autre";
}

// ==================== FONCTIONS ====================

/**
 * Récupère la liste paginée des factures.
 */
export async function getInvoices(
  params: GetInvoicesParams = {}
): Promise<InvoiceListResponse> {
  const response = await api.get<InvoiceListResponse>("/api/invoices", {
    params,
  });
  return response.data;
}

/**
 * Récupère le détail d'une facture par son ID.
 */
export async function getInvoiceById(id: number): Promise<InvoiceResponse> {
  const response = await api.get<InvoiceResponse>(`/api/invoices/${id}`);
  return response.data;
}

/**
 * Supprime une facture.
 */
export async function deleteInvoice(id: number): Promise<{ id: number; status: string }> {
  const response = await api.delete(`/api/invoices/${id}`);
  return response.data;
}

/**
 * Ouvre le téléchargement du JSON d'une facture dans un nouvel onglet.
 */
export function downloadInvoice(id: number): void {
  window.open(`${API_BASE_URL}/api/invoices/${id}/export`, "_blank");
}


// ==================== MISE À JOUR ====================

export interface UpdateInvoicePayload {
  supplier?: string | null;
  invoice_number?: string | null;
  date?: string | null;
  total_ht?: number | null;
  vat?: number | null;
  total_ttc?: number | null;
}

/**
 * Met à jour les données extraites d'une facture (correction manuelle).
 */
export async function updateInvoice(
  id: number,
  payload: UpdateInvoicePayload
): Promise<InvoiceResponse> {
  const response = await api.put<InvoiceResponse>(`/api/invoices/${id}`, payload);
  return response.data;
}
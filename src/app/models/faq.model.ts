export interface FAQItem {
  id: number;
  question: string;
  answer: string;
  category: string;
  is_active?: boolean;
  display_order?: number;
  created_at?: string;
  updated_at?: string;
}

export interface FAQListResponse {
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: FAQItem[];
}

export interface FAQQueryParams {
  category?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}

export interface FAQCreatePayload {
  question: string;
  answer: string;
  category?: string | null;
  is_active?: boolean;
  display_order?: number;
}

export interface FAQUpdatePayload {
  question?: string | null;
  answer?: string | null;
  category?: string | null;
  is_active?: boolean | null;
  display_order?: number | null;
}

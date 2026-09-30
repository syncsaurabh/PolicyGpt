export interface SourceCitation {
  type: 'scheme' | 'policy' | 'faq' | 'eligibility' | 'comparison' | 'support' | string;
  id?: number | string | null;
  name: string;
  category?: string | null;
  url?: string | null;
  snippet?: string | null;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string | null;
  profile_context?: Record<string, any> | null;
}

export interface ChatResponse {
  answer: string;
  conversation_id: string;
  intent: string;
  sources?: SourceCitation[];
  suggested_questions?: string[];
  created_at?: string;
}

export interface ConversationListItem {
  id: string;
  title: string;
  last_message?: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationListResponse {
  total_count: number;
  results: ConversationListItem[];
}

export interface ConversationMessageRead {
  id: number;
  role: 'user' | 'assistant' | string;
  content: string;
  sources?: SourceCitation[];
  intent?: string | null;
  created_at: string;
}

export interface ConversationDetailResponse {
  id: string;
  title: string;
  user_id?: number | null;
  created_at: string;
  updated_at: string;
  messages: ConversationMessageRead[];
}

export interface AssistantChatMessage {
  id?: number | string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceCitation[];
  intent?: string | null;
  created_at?: string;
  suggested_questions?: string[];
  isError?: boolean;
}

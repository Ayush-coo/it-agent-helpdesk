export type ChatRequest = {
  message: string;
  conversation_id?: string | null;
  ticket_id?: string | null;
  context?: string | null;
  use_knowledge_base?: boolean;
};

export type ChatTicket = {
  id: string;
  ticket_number: string;
  status: string;
};

export type ChatReference = {
  id: string;
  title: string;
  source?: string | null;
  snippet: string;
  score: number;
};

export type ChatResponse = {
  reply: string;
  model: string;
  provider: string;
  references: ChatReference[];
  conversation_id: string | null;
  ticket: ChatTicket | null;
  pending_action: string | null;
  mock_otp: string | null;
};

export type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  references?: ChatReference[];
  ticket?: ChatTicket | null;
  pendingAction?: string | null;
  mockOtp?: string | null;
};
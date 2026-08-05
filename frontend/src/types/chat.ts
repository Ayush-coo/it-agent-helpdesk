export type ChatRequest = {
  message: string;
  ticket_id?: string | null;
  context?: string | null;
  use_knowledge_base?: boolean;
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
};

export type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  references?: ChatReference[];
};
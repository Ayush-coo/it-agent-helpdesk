export type KnowledgeBaseIngestRequest = {
  title: string;
  content: string;
  source?: string | null;
  tags: string[];
};

export type KnowledgeBaseDocument = {
  id: string;
  title: string;
  content: string;
  source?: string | null;
  tags: string[];
  created_at: string;
};

export type KnowledgeBaseSearchResult = {
  id: string;
  title: string;
  source?: string | null;
  tags: string[];
  snippet: string;
  score: number;
};

export type KnowledgeBaseSearchResponse = {
  query: string;
  results: KnowledgeBaseSearchResult[];
};
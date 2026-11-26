export type TicketStatus = 'open' | 'in_progress' | 'waiting_on_user' | 'resolved' | 'closed';

export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';

export type TicketSeverity = 'P1' | 'P2' | 'P3' | 'P4';

export type EscalationStatus = 'none' | 'pending_review' | 'approved' | 'rejected' | 'auto_resolved';

export type TicketRead = {
  id: string;
  ticket_number: string;
  title: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  severity: TicketSeverity;
  requester_id: string;
  assigned_to_id?: string | null;
  category?: string | null;
  escalation_status: EscalationStatus;
  created_at: string;
  updated_at: string;
};

export type TicketComment = {
  id: string;
  ticket_id: string;
  author_id: string;
  body: string;
  is_internal: boolean;
  created_at: string;
};

export type TicketEvent = {
  id: string;
  ticket_id: string;
  actor_id: string | null;
  type: string;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
};

export type TicketStatusCount = {
  status: TicketStatus;
  count: number;
};

export type TicketOverview = {
  scope: string;
  total: number;
  status_counts: TicketStatusCount[];
  recent_tickets: TicketRead[];
  refreshed_at: string;
};
export interface KnowledgeBase {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  color: string | null;
  is_system: boolean;
  source_count: number;
  wiki_page_count: number;
  created_at: string;
}

export interface Source {
  id: string;
  kb_id: string;
  url: string;
  title: string | null;
  status: "pending" | "processing" | "completed" | "failed";
  fetched_at: string | null;
  created_at: string;
}

export interface SourceDetail extends Source {
  raw_content: string | null;
}

export interface WikiPage {
  id: string;
  kb_id: string;
  slug: string;
  title: string;
  page_type: string;
  content: string | null;
  source_ids: string[] | null;
  outgoing_links: string[] | null;
  incoming_links: string[] | null;
  created_at: string;
}

export interface WikiPageListItem {
  id: string;
  slug: string;
  title: string;
  page_type: string;
  created_at: string;
}

export interface Notification {
  id: string;
  kb_id: string;
  kb_slug: string | null;
  source_id: string;
  trigger_type: string;
  title: string;
  summary: string | null;
  related_points: string[] | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationList {
  items: Notification[];
  unread_count: number;
}

export interface GraphData {
  nodes: { id: string; slug: string; title: string; type: string }[];
  edges: { source: string; target: string }[];
}

export interface ChatMessage {
  question: string;
  answer: string;
  referenced_pages: { slug: string; title: string }[];
}

export interface GeneratedDoc {
  id: string;
  title: string;
  topic: string;
  content: string | null;
  kb_ids: string[] | null;
  status: "generating" | "completed" | "failed";
  word_count: number;
  created_at: string;
}

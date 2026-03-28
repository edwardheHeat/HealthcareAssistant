export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: number;
  session_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: number;
  user_id: number;
  started_at: string;
}

export interface ChatResponse {
  message: ChatMessage;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
}
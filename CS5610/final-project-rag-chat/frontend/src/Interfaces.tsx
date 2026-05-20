
/**
 * Interface for a reference used in chat messages.
 */
export interface Reference {
  refId: string;
  title: string;
  author: string;
  page: number;
  content: string;
  score: number;
}

/**
 * Interface for a message in the chat application.
 */
export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  references?: Reference[];
}

/**
 * Interface for a summary of a chat session.
 */
export interface ChatSummary {
  id: string;
  preview: string;
  updatedAt: string;
}

/**
 * Interface for chat settings.
 */
export interface ChatSettings {
  professionalMode: boolean;
  topK: number;
  similarityThreshold: number;
}

/**
 * Interface for authentication action responses.
 */
export interface AuthActionResponse {
  success: boolean;
  message?: string;
  username?: string;
}
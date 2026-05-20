import type { AuthActionResponse, ChatSettings, ChatSummary } from './Interfaces';

/**
 * Base URL for API requests.
 * Defaults to '/api' if VITE_API_BASE is not set.
 */
export const API_BASE = import.meta.env.VITE_API_BASE || '/api';

/**
 * Service for handling API requests to the backend.
 */
export const apiService = {
  async checkAuth() {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        return { authenticated: true, username: data.user?.username };
      }
      return { authenticated: false };
    } catch {
      return { authenticated: false };
    }
  },

  async signIn(username: string, password: string): Promise<AuthActionResponse> {
    try {
      const res = await fetch(`${API_BASE}/auth/signin`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) return { success: false, message: data.message || 'Sign in failed' };
      return { success: true, username: data.user?.username };
    } catch {
      return { success: false, message: 'Network error' };
    }
  },

  async signUp(username: string, password: string): Promise<AuthActionResponse> {
    try {
      const res = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) return { success: false, message: data.message || 'Sign up failed' };
      return { success: true, username: data.user?.username };
    } catch {
      return { success: false, message: 'Network error' };
    }
  },

  async signOut(): Promise<AuthActionResponse> {
    try {
      await fetch(`${API_BASE}/auth/signout`, { method: 'POST', credentials: 'include' });
      return { success: true, message: 'Signed out' };
    } catch {
      return { success: false, message: 'Network error' };
    }
  },

  async listChats(): Promise<ChatSummary[]> {
    try {
      const res = await fetch(`${API_BASE}/chats`, { credentials: 'include' });
      const data = await res.json();
      return data.chats || [];
    } catch { return []; }
  },

  async createChat(settings: ChatSettings): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/chats`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings }),
      });
      const data = await res.json();
      return res.ok ? data.chat : null;
    } catch { return null; }
  },

  async getChat(chatId: string): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/chats/${chatId}`, { credentials: 'include' });
      const data = await res.json();
      return res.ok ? data.chat : null;
    } catch { return null; }
  },

  async deleteChat(chatId: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/chats/${chatId}`, { method: 'DELETE', credentials: 'include' });
      return res.ok;
    } catch { return false; }
  },

  async updateChat(chatId: string, updates: any): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/chats/${chatId}`, {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      return res.ok;
    } catch { return false; }
  },

  async uploadDocuments(file: File): Promise<{ success: boolean; message?: string }> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });
      const data = await res.json();
      return { success: res.ok, message: data.message };
    } catch { return { success: false, message: 'Network error' }; }
  },

  async deleteDocuments(): Promise<{ success: boolean; message?: string }> {
    try {
      const res = await fetch(`${API_BASE}/documents/delete`, { method: 'DELETE', credentials: 'include' });
      const data = await res.json();
      return { success: res.ok, message: data.message };
    } catch { return { success: false, message: 'Network error' }; }
  },

  async getDocumentCount(): Promise<number> {
    try {
      const res = await fetch(`${API_BASE}/documents/count`, { credentials: 'include' });
      const data = await res.json();
      return res.ok ? data.count || 0 : 0;
    } catch { return 0; }
  },
};
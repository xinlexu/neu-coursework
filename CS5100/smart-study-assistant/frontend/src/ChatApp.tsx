/* =============================================================================
   RAG Chat Application
============================================================================= */

import { useState, useEffect, useRef } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import { Loader2 } from 'lucide-react';
import type { ChatSettings, ChatSummary, Message, Reference } from './Interfaces';
import { apiService, API_BASE } from './Apis.tsx';
import { AuthScreen } from './Components/AuthScreen';
import { AboutModal } from './Components/AboutModel.tsx';
import { ChatList } from './Components/ChatList.tsx';
import { MainChatHeader } from './Components/MainChatHeader.tsx';
import { MessageList } from './Components/MessageList.tsx';
import { InputArea } from './Components/InputArea.tsx';
import { Settings } from './Components/Settings.tsx';

// --------------------------------------------- Global ---------------------------------------------
/**
 * Default settings for the chat application.
 */
const DEFAULT_SETTINGS: ChatSettings = {
  professionalMode: false,
  topK: 5,
  similarityThreshold: 0.6,
};

// --- Main App ---

export default function ChatApp() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [user, setUser] = useState('');
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [docCount, setDocCount] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showAbout, setShowAbout] = useState(false);

  // Refs
  const abortController = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Initial Load
  useEffect(() => {
    apiService.checkAuth().then(({ authenticated, username }) => {
      setIsAuthenticated(authenticated);
      if (authenticated && username) setUser(username);
    });
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      refreshData();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const refreshData = async () => {
    const [c, d] = await Promise.all([apiService.listChats(), apiService.getDocumentCount()]);
    setChats(c);
    setDocCount(d);
  };

  const handleSignIn = async (u: string, p: string) => {
    const res = await apiService.signIn(u, p);
    if (res.success) {
      setUser(res.username || u);
      setIsAuthenticated(true);
    }
    return res;
  };

  const handleSignUp = async (u: string, p: string) => {
    const res = await apiService.signUp(u, p);
    if (res.success) {
      setUser(res.username || u);
      setIsAuthenticated(true);
    }
    return res;
  };

  const handleSignOut = async () => {
    await apiService.signOut();
    setIsAuthenticated(false);
    setMessages([]);
    setActiveChat(null);
  };

  const handleNewChat = async () => {
    const chat = await apiService.createChat(settings);
    if (chat) {
      setActiveChat(chat.chatId);
      setMessages(chat.messages);
      setSettings(chat.settings);
      refreshData();
    }
  };

  const handleLoadChat = async (id: string) => {
    const chat = await apiService.getChat(id);
    if (chat) {
      setActiveChat(chat.chatId);
      setMessages(chat.messages);
      setSettings(chat.settings);
    }
  };

  const handleDeleteChat = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('Delete this chat?')) {
      await apiService.deleteChat(id);
      if (activeChat === id) {
        setActiveChat(null);
        setMessages([]);
      }
      refreshData();
      toast.success('Chat deleted');
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;
    const prompt = input.trim();
    setInput('');

    let chatId = activeChat;
    if (!chatId) {
      const chat = await apiService.createChat(settings);
      if (!chat) return;
      chatId = chat.chatId;
      setActiveChat(chatId);
      refreshData();
    }

    const newMsgs = [...messages, { role: 'user', content: prompt } as Message];
    setMessages(newMsgs);
    setIsStreaming(true);
    abortController.current = new AbortController();

    try {
      const res = await fetch(`${API_BASE}/chats/${chatId}/stream`, {
        method: 'POST',
        credentials: 'include', // Need credentials
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userPrompt: prompt, settings }),
        signal: abortController.current.signal,
      });

      if (!res.ok) throw new Error(res.statusText);

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let assistantMsg = { role: 'assistant', content: '', references: [] } as Message;
      let tempReferencesCache: Reference[] = []; // Store references temporarily

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            try {
              const parsed = JSON.parse(data);
              if (parsed.type === 'content') {
                assistantMsg.content += parsed.text;
                setMessages([...newMsgs, { ...assistantMsg }]); // Reference is empty during strem, will not show
              } else if (parsed.type === 'references') {
                tempReferencesCache = parsed.references;        // Reference is stored in temp cache, will be filtered before updating
              } else if (parsed.type === 'error') {
                toast.error(parsed.message);
              }
            } catch {}
          }
        }
      }
      // After stream completes, retrieved the used references indices from the content
      const usedRefIds = new Set(
          (assistantMsg.content.match(/\[\d+\]/g) || [])
              .map(match => match.slice(1, -1))
      );
      // If there are used references and pending references
      if (usedRefIds.size > 0 && tempReferencesCache.length > 0) {
          // Filter to only used references, relative order of references is preserved
          const usedRefs = tempReferencesCache.filter(ref => usedRefIds.has(ref.refId));
          // Map original reference indices to contiguous indices
          // e.g., LLM stream could contain citation marker in non-contiguous order like [1][3][1]
          // Map them to contiguous indices like [1][2][1]
          // Non-monotonic order is allowed
          const indexMap: Record<string, string> = {};
          usedRefs.forEach((ref, i) => {
              indexMap[ref.refId] = (i + 1).toString();
          });
          // Reindex references
          assistantMsg.references = usedRefs.map((ref, i) => ({
              ...ref,
              refId: (i + 1).toString()
          }));
          // Repair citations in content: [3] -> [1], [5] -> [2], etc.
          assistantMsg.content = assistantMsg.content.replace(
              /\[(\d+)\]/g,
              (match, num) => indexMap[num] ? `[${indexMap[num]}]` : match
          );
      }
      // Update messages with processed references
      setMessages([...newMsgs, assistantMsg]);
      if (chatId) {
        await apiService.updateChat(chatId, { messages: [...newMsgs, assistantMsg] });
      }
      refreshData();
    } catch (err: any) {
      if (err.name !== 'AbortError') toast.error('Stream failed');
    } finally {
      setIsStreaming(false);
      abortController.current = null;
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.jsonl')) {
      toast.error('Only .jsonl files are supported');
      return;
    }

    const toastId = toast.loading('Uploading documents...');
    const res = await apiService.uploadDocuments(file);
    if (res.success) {
      toast.success(`Uploaded: ${file.name}`, { id: toastId });
      refreshData();
    } else {
      toast.error(res.message || 'Upload failed', { id: toastId });
    }
    e.target.value = '';
  };

  const handleDeleteDocs = async () => {
    if (!confirm('Delete ALL documents? This cannot be undone.')) return;
    const toastId = toast.loading('Deleting documents...');
    const res = await apiService.deleteDocuments();
    if (res.success) {
      toast.success('All documents deleted', { id: toastId });
      refreshData();
    } else {
      toast.error(res.message || 'Delete failed', { id: toastId });
    }
  };

  if (isAuthenticated === null) return <div className="h-screen bg-background flex items-center justify-center text-neutral-500"><Loader2 className="animate-spin" /></div>;
  if (!isAuthenticated) return <AuthScreen onSignIn={handleSignIn} onSignUp={handleSignUp} />;

  return (
    <div className="flex h-screen bg-background text-neutral-200 font-sans selection:bg-blue-500/30">
      <Toaster position="top-center" toastOptions={{ style: { background: '#333', color: '#fff' } }} />
      <AboutModal isOpen={showAbout} onClose={() => setShowAbout(false)} />
      {/* Left sidebar for chat list */}
      <ChatList
        sidebarOpen={sidebarOpen}
        handleNewChat={handleNewChat}
        handleLoadChat={handleLoadChat}
        handleDeleteChat={handleDeleteChat}
        handleSignOut={handleSignOut}
        chats={chats}
        user={user}
        activeChat={activeChat}
      />
      {/* Main Area */}
      <main className="flex-1 flex flex-col min-w-0 relative">
        {/* Header */}
        <MainChatHeader
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          setShowAbout={setShowAbout}
          settings={settings}
          docCount={docCount}
        />
        {/* Message List */}
        <MessageList
          messages={messages}
          isStreaming={isStreaming}
          scrollRef={scrollRef}
        />
        {/* Input Area */}
        <InputArea
          input={input}
          setInput={setInput}
          handleSend={handleSend}
          isStreaming={isStreaming}
          abortController={abortController}
        />
        {/* Right Settings Panel */}
        <Settings
          settings={settings}
          setSettings={setSettings}
          activeChat={activeChat}
          handleUpload={handleUpload}
          handleDeleteDocs={handleDeleteDocs}
        />
      </main>
    </div>
  );
}
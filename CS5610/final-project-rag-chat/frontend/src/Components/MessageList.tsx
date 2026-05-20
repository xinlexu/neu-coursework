import { Settings2, MessageSquare, UploadCloud, Loader2, Bot } from 'lucide-react';
import type { Message } from '../Interfaces';
import { MessageBubble } from './MessageBubble';

/**
 * MessageList component for the chat application message list.
 * @param messages - Array of message objects to be rendered.
 * @param isStreaming - Whether the chat is currently streaming.
 * @param scrollRef - Reference to the scroll container element.
 * @returns JSX element for the MessageList component.
 */
export function MessageList({ messages, isStreaming, scrollRef }: { 
    messages: Message[], 
    isStreaming: boolean, 
    scrollRef: React.Ref<HTMLDivElement> | undefined
}) {
    return (
        <div className="flex-1 overflow-y-auto p-4 md:p-6 scroll-smooth">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-8 max-w-2xl mx-auto animate-in fade-in zoom-in-95 duration-500">
              <div className="w-16 h-16 bg-surface rounded-2xl flex items-center justify-center shadow-lg border border-neutral-800 mb-6">
                <Bot size={32} className="text-neutral-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Welcome to Smart Study Assistant</h2>
              <p className="text-neutral-400 text-center mb-8 max-w-md">
                Your AI-powered research companion. Upload your study materials and ask questions with citation-backed answers.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
                <div className="bg-surface/50 border border-neutral-800 p-4 rounded-xl flex flex-col items-center text-center">
                  <div className="bg-neutral-800 p-2 rounded-lg mb-3 text-neutral-300"><Settings2 size={20} /></div>
                  <h3 className="text-sm font-semibold text-white mb-1">Toggle Mode</h3>
                  <p className="text-xs text-neutral-500">Enable Professional Mode in settings to activate RAG.</p>
                </div>
                <div className="bg-surface/50 border border-neutral-800 p-4 rounded-xl flex flex-col items-center text-center">
                  <div className="bg-neutral-800 p-2 rounded-lg mb-3 text-neutral-300"><UploadCloud size={20} /></div>
                  <h3 className="text-sm font-semibold text-white mb-1">Upload Data</h3>
                  <p className="text-xs text-neutral-500">Upload your .jsonl files to build your knowledge base.</p>
                </div>
                <div className="bg-surface/50 border border-neutral-800 p-4 rounded-xl flex flex-col items-center text-center">
                  <div className="bg-neutral-800 p-2 rounded-lg mb-3 text-neutral-300"><MessageSquare size={20} /></div>
                  <h3 className="text-sm font-semibold text-white mb-1">Ask Away</h3>
                  <p className="text-xs text-neutral-500">Get precise answers with references to your documents.</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto">
              {messages.map((m, i) => <MessageBubble key={i} message={m} />)}
              {isStreaming && (
                <div className="flex items-center gap-2 text-neutral-500 text-xs ml-12 animate-pulse">
                  <Loader2 size={12} className="animate-spin" /> Thinking...
                </div>
              )}
              <div ref={scrollRef} />
            </div>
          )}
        </div>
    )
};
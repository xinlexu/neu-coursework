import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import type { Message } from '../Interfaces';
import { cn } from '../Utils';
import { User, BookOpen, Bot } from 'lucide-react';

/**
 * Component for rendering a message bubble in the chat interface.
 * @param message - The message object to be rendered.
 * @returns The rendered message bubble component.
 */
export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  
  return (
    <div className={cn("flex w-full mb-6 animate-in slide-in-from-bottom-2 duration-300", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-green-600/20 text-green-500 flex items-center justify-center mr-4 mt-1 shrink-0">
          <Bot size={18} />
        </div>
      )}
      
      <div className={cn("max-w-[85%] lg:max-w-[75%]")}>
        <div className={cn(
          "px-5 py-3.5 rounded-2xl text-sm leading-relaxed shadow-sm",
          isUser 
            ? "bg-blue-600 text-white rounded-br-sm" 
            : "bg-surface border border-neutral-800 text-neutral-200 rounded-bl-sm"
        )}>
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none prose-p:my-1.5 prose-pre:bg-neutral-900 prose-pre:border prose-pre:border-neutral-800">
              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                {message.content.replace(/\[(\d+)\]/g, '<span class="text-blue-400 font-bold mx-0.5">[$1]</span>')}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* References Section */}
        {message.references && message.references.length > 0 && (
          <div className="mt-3 grid gap-2 animate-in fade-in duration-500">
            <div className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <BookOpen size={14} /> Citations
            </div>
            {message.references.map((ref, idx) => (
              <div key={idx} className="bg-surface/50 border border-neutral-800 rounded-lg p-3 text-xs hover:border-neutral-700 transition-colors">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-medium text-blue-400 flex items-center gap-1.5">
                    <span className="bg-blue-500/10 px-1.5 py-0.5 rounded text-[10px]">REF {ref.refId}</span>
                    {ref.title}
                  </span>
                  <span className="text-green-500/80 font-mono text-[10px]">{Math.round(ref.score * 100)}% Match</span>
                </div>
                <div className="text-neutral-400 mb-1">
                  by <span className="text-neutral-300">{ref.author}</span> • Page {ref.page}
                </div>
                <div className="text-neutral-500 italic line-clamp-2 border-l-2 border-neutral-800 pl-2">
                  "{ref.content}"
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white ml-4 mt-1 shrink-0">
          <User size={18} />
        </div>
      )}
    </div>
  );
};
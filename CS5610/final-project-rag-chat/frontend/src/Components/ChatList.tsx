import {cn} from '../Utils';
import type { ChatSummary } from '../Interfaces';
import { Plus, Trash2, User, LogOut, MessageSquare } from 'lucide-react';

/**
 * ChatList component for the chat application sidebar.
 * @param sidebarOpen - Whether the sidebar is open.
 * @param handleNewChat - Function to handle creating a new chat.
 * @param handleLoadChat - Function to handle loading a chat.
 * @param handleDeleteChat - Function to handle deleting a chat.
 * @param handleSignOut - Function to handle sign-out.
 * @param chats - Array of chat summaries.
 * @param user - Current user's name.
 * @param activeChat - ID of the currently active chat.
 * @returns JSX.Element
 */
export function ChatList({ sidebarOpen, handleNewChat, handleLoadChat, handleDeleteChat, handleSignOut, chats, user, activeChat }: {
  sidebarOpen: boolean;
  handleNewChat: () => void;
  handleLoadChat: (chatId: string) => void;
  handleDeleteChat: (e: React.MouseEvent, chatId: string) => void;
  handleSignOut: () => void;
  chats: ChatSummary[];
  user: string;
  activeChat: string | null;
}) {
    return (
      <aside className={cn(
        "w-[280px] bg-surface border-r border-neutral-800 flex flex-col transition-all duration-300",
        !sidebarOpen && "-ml-[280px]"
      )}>
        <div className="p-4 border-b border-neutral-800">
          <button 
            onClick={handleNewChat}
            className="w-full bg-neutral-800 hover:bg-neutral-700 text-white font-medium py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors border border-neutral-700"
          >
            <Plus size={18} /> New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <div className="px-2 py-1.5 text-xs font-semibold text-neutral-500 uppercase tracking-wider">History</div>
          {chats.map(chat => (
            <div
              key={chat.id}
              onClick={() => handleLoadChat(chat.id)}
              className={cn(
                "group flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all",
                activeChat === chat.id ? "bg-neutral-800 text-white" : "text-neutral-400 hover:bg-neutral-800/50 hover:text-neutral-200"
              )}
            >
              <MessageSquare size={16} />
              <div className="flex-1 truncate text-sm">{chat.preview || "New Chat"}</div>
              <button 
                onClick={(e) => handleDeleteChat(e, chat.id)}
                className="opacity-0 group-hover:opacity-100 text-neutral-500 hover:text-red-400 transition-opacity p-1"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-neutral-800 bg-surface">
          <div className="flex items-center gap-3 px-2 py-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-blue-900/50 text-blue-400 flex items-center justify-center border border-blue-900">
              <User size={16} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-white truncate">{user}</div>
            </div>
            <button onClick={handleSignOut} className="text-neutral-500 hover:text-white transition-colors" title="Sign out">
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>
    )
};
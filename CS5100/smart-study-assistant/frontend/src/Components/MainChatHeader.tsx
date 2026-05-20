import { Settings2, FileText, Sparkles, Info } from 'lucide-react';
import type { ChatSettings } from '../Interfaces';

/**
 * MainChatHeader component for the chat application header.
 * @param sidebarOpen - Whether the sidebar is open or not.
 * @param setSidebarOpen - Function to set the sidebar open state.
 * @param setShowAbout - Function to set the about modal state.
 * @param settings - Chat settings.
 * @param docCount - Number of documents uploaded.
 * @returns JSX element for the MainChatHeader component.
 */
export function MainChatHeader({ sidebarOpen, setSidebarOpen, setShowAbout, settings, docCount }: {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  setShowAbout: (show: boolean) => void;
  settings: ChatSettings;
  docCount: number;
}) {
    return (
        <header className="h-14 border-b border-neutral-800 flex items-center justify-between px-4 bg-background/80 backdrop-blur z-10">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-neutral-400 hover:text-white">
              <Settings2 size={20} />
            </button>
            <span className="font-medium text-sm flex items-center gap-2">
              {settings.professionalMode ? (
                <span className="bg-blue-600/10 text-blue-400 border border-blue-600/20 px-2 py-0.5 rounded text-xs font-semibold flex items-center gap-1">
                  <Sparkles size={10} /> Professional
                </span>
              ) : (
                <span className="text-neutral-500 text-xs">Standard Mode</span>
              )}
            </span>
          </div>

          <div className="absolute left-1/2 -translate-x-1/2 font-semibold text-sm hidden md:block text-neutral-200">
            Smart Study Assistant
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 text-xs text-neutral-500 bg-surface border border-neutral-800 px-3 py-1.5 rounded-full">
              <FileText size={12} />
              <span>{docCount} Docs</span>
            </div>
            <button
              onClick={() => setShowAbout(true)}
              className="text-neutral-400 hover:text-white transition-colors p-1"
              title="About & Authors"
            >
              <Info size={20} />
            </button>
          </div>
        </header>
    )
};
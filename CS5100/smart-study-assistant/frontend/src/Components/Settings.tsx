import type { ChatSettings } from '../Interfaces.tsx';
import { apiService } from '../Apis.tsx';
import { cn } from '../Utils.tsx';
import { Trash2, Settings2, UploadCloud } from 'lucide-react';

export function Settings({ settings, setSettings, activeChat, handleUpload, handleDeleteDocs}: {
    settings: ChatSettings,
    setSettings: React.Dispatch<React.SetStateAction<ChatSettings>>
    activeChat: string | null,
    handleUpload: React.ChangeEventHandler<HTMLInputElement>,
    handleDeleteDocs: React.MouseEventHandler<HTMLButtonElement>
}) {
    return (
        <div className="absolute top-14 right-4 w-64 bg-surface/90 backdrop-blur border border-neutral-800 rounded-xl p-4 shadow-2xl hidden md:block animate-in fade-in slide-in-from-right-5">
          <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Settings2 size={14} /> Configuration
          </h3>
          {/* Professional Mode */}
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <label className="text-sm text-neutral-300 font-medium">Professional Mode</label>
              <button
                onClick={() => {
                  const newVal = !settings.professionalMode;
                  setSettings(s => ({ ...s, professionalMode: newVal }));
                  if(activeChat) apiService.updateChat(activeChat, { settings: { ...settings, professionalMode: newVal }});
                }}
                className={cn("w-9 h-5 rounded-full relative transition-colors", settings.professionalMode ? "bg-blue-600" : "bg-neutral-700")}
              >
                <div className={cn("w-3 h-3 bg-white rounded-full absolute top-1 transition-all", settings.professionalMode ? "left-5" : "left-1")} />
              </button>
            </div>

            {/* Top K slider */}
            <div className={cn("space-y-4 transition-opacity", !settings.professionalMode && "opacity-40 pointer-events-none")}>
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-neutral-400">
                  <span>Top K</span>
                  <span>{settings.topK}</span>
                </div>
                <input
                  type="range" min="1" max="10"
                  value={settings.topK}
                  onChange={(e) => setSettings(s => ({...s, topK: Number(e.target.value)}))}
                  onMouseUp={() => activeChat && apiService.updateChat(activeChat, { settings })}
                  className="w-full h-1 bg-neutral-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <div className="text-[10px] text-neutral-500 pt-1">Number of documents to retrieve</div>
              </div>

              {/* Threshold slider */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-neutral-400">
                  <span>Threshold</span>
                  <span>{settings.similarityThreshold}</span>
                </div>
                <input
                  type="range" min="0" max="1" step="0.05"
                  value={settings.similarityThreshold}
                  onChange={(e) => setSettings(s => ({...s, similarityThreshold: Number(e.target.value)}))}
                  onMouseUp={() => activeChat && apiService.updateChat(activeChat, { settings })}
                  className="w-full h-1 bg-neutral-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <div className="text-[10px] text-neutral-500 pt-1">Minimum score for retrieved docs</div>
              </div>

              <div className="pt-2 border-t border-neutral-800">
                <label className="flex items-center justify-center gap-2 w-full py-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs font-medium rounded-lg cursor-pointer transition-colors border border-neutral-700">
                  <UploadCloud size={14} /> Upload Knowledge
                  <input type="file" className="hidden" accept=".jsonl" onChange={handleUpload} />
                </label>
                <div className="text-[10px] text-neutral-500 pt-1 text-center">Supports .jsonl files only</div>
              </div>

              <button
                onClick={handleDeleteDocs}
                className="flex items-center justify-center gap-2 w-full py-2 bg-red-900/20 hover:bg-red-900/40 text-red-400 text-xs font-medium rounded-lg transition-colors border border-red-900/30"
              >
                <Trash2 size={14} /> Clear Database
              </button>
            </div>
          </div>
        </div>
    )
};
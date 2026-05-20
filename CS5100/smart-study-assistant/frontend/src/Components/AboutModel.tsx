import { Sparkles, X, Github } from 'lucide-react';

/**
 * Modal component for displaying application information.
 * @param isOpen - Whether the modal is open.
 * @param onClose - Function to close the modal.
 * @returns The rendered AboutModal component.
 */
export function AboutModal({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-surface border border-neutral-800 rounded-2xl shadow-2xl p-6 relative animate-in zoom-in-95 duration-200 m-4">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-neutral-500 hover:text-white transition-colors"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-14 h-14 bg-blue-600/20 text-blue-500 rounded-2xl flex items-center justify-center mb-4">
            <Sparkles size={32} />
          </div>
          <h2 className="text-xl font-bold text-white">Smart Study Assistant</h2>
          <p className="text-sm text-neutral-500 mt-1">CS5100 Project</p>
        </div>

        <div className="space-y-4">
          <div className="bg-neutral-900/50 rounded-xl p-4 border border-neutral-800/50">
            <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-3">Course</h3>
            <div className="text-sm font-medium text-neutral-200">CS5100 - Intro to AI</div>
          </div>

          <a
            href="https://github.com/xinlexu/neu-coursework/tree/main/CS5100/smart-study-assistant"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-3 bg-neutral-800 hover:bg-neutral-700 text-white rounded-xl transition-all border border-neutral-700 font-medium text-sm"
          >
            <Github size={18} /> View Source Code
          </a>
        </div>
      </div>
    </div>
  );
};

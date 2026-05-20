import { Send, StopCircle } from 'lucide-react';
import { cn } from '../Utils';

/**
 * InputArea component for the chat application.
 * @param input - The current input value.
 * @param setInput - Function to update the input value.
 * @param handleSend - Function to handle sending the message.
 * @param isStreaming - Whether the chat is currently streaming a response.
 * @param abortController - React ref object for the AbortController to handle streaming cancellation.
 */
export function InputArea({ 
  input, 
  setInput, 
  handleSend, 
  isStreaming, 
  abortController 
}: { 
  input: string, 
  setInput: (value: string) => void, 
  handleSend: () => void, 
  isStreaming: boolean, 
  abortController: React.RefObject<AbortController | null>
}) {
    return (
        <div className="p-4 border-t border-neutral-800 bg-background">
          <div className="max-w-3xl mx-auto">
            <div className="relative bg-surface border border-neutral-700 rounded-xl shadow-lg focus-within:ring-1 focus-within:ring-blue-600/50 transition-all">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Message..."
                className="w-full bg-transparent text-white px-4 py-3 pr-12 text-sm max-h-40 min-h-[52px] resize-none focus:outline-none scrollbar-hide"
                rows={1}
                disabled={isStreaming}
              />
              <button 
                onClick={isStreaming ? () => abortController.current?.abort() : handleSend}
                disabled={!input.trim() && !isStreaming}
                className={cn(
                  "absolute right-2 bottom-2 p-1.5 rounded-lg transition-colors",
                  input.trim() || isStreaming ? "bg-blue-600 text-white" : "bg-neutral-700 text-neutral-500 cursor-not-allowed"
                )}
              >
                {isStreaming ? <StopCircle size={16} /> : <Send size={16} />}
              </button>
            </div>
            <div className="text-[10px] text-neutral-500 text-center mt-2">
              AI can make mistakes. Please verify important information.
            </div>
          </div>
        </div>
    )
};
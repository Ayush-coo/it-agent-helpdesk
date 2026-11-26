import ReactMarkdown from 'react-markdown';
import type { ChatMessage as ChatMessageType } from '../../types/chat';
import { Bot, User as UserIcon } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
  pendingAction: string | null;
  isLatestPendingAction: boolean;
  isStreaming: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ChatMessage({
  message,
  pendingAction,
  isLatestPendingAction,
  isStreaming,
  onConfirm,
  onCancel,
}: ChatMessageProps) {
  const isAssistant = message.role === 'assistant';

  return (
    <div className={`w-full py-6 px-4 ${isAssistant ? '' : ''}`}>
      <div className="max-w-3xl mx-auto flex items-start gap-4 md:gap-6">
        
        {/* Avatar */}
        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
          isAssistant ? 'bg-emerald-600' : 'bg-gray-600'
        }`}>
          {isAssistant ? (
            <Bot size={18} className="text-white" />
          ) : (
            <UserIcon size={18} className="text-white" />
          )}
        </div>
        
        {/* Message Content */}
        <div className="flex-1 min-w-0 flex flex-col justify-center pt-1">
          {isAssistant ? (
            <div className="prose prose-invert prose-p:leading-relaxed prose-pre:bg-[#1a1a1a] prose-pre:border prose-pre:border-gray-800 w-full max-w-none text-gray-200">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          ) : (
            <div className="whitespace-pre-wrap text-gray-200 leading-relaxed">
              {message.content}
            </div>
          )}

          {/* References */}
          {isAssistant && message.references && message.references.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-800 w-full space-y-2">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Sources</div>
              <div className="flex flex-wrap gap-2">
                {message.references.map((ref) => (
                  <div key={ref.id} className="bg-[#2f2f2f] border border-gray-700 rounded text-xs text-gray-300 px-2 py-1 flex items-center gap-2">
                    <span className="font-medium truncate max-w-[200px]">{ref.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {isAssistant && message.ticket && (
            <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-emerald-700 bg-emerald-950/60 px-3 py-1 text-xs text-emerald-200">
              <span className="font-semibold">{message.ticket.ticket_number}</span>
              <span className="capitalize">{message.ticket.status.replace(/_/g, ' ')}</span>
            </div>
          )}
          {isAssistant && isLatestPendingAction && message.pendingAction && message.pendingAction === pendingAction && (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <span className="text-sm text-amber-300">
                Demo OTP: <strong>{message.mockOtp}</strong>
              </span>
              <button
                type="button"
                onClick={onConfirm}
                disabled={isStreaming}
                className="rounded-lg bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
              >
                Confirm
              </button>
              <button
                type="button"
                onClick={onCancel}
                disabled={isStreaming}
                className="rounded-lg border border-gray-600 px-3 py-1.5 text-sm text-gray-200 disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
}

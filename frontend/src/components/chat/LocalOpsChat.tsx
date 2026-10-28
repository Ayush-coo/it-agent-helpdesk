import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { ArrowUp, Bot } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useLocalOpsStream } from '../../hooks/useLocalOpsStream';
import ChatMessage from './ChatMessage';

export default function LocalOpsChat() {
  const { token } = useAuth();
  const [inputText, setInputText] = useState('');
  const { messages, sendMessage, isStreaming, error } = useLocalOpsStream(token);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputText]);

  const handleSend = () => {
    if (!inputText.trim() || isStreaming) return;
    sendMessage(inputText);
    setInputText('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto pb-32">
        {messages.length === 1 ? (
          <div className="h-full flex flex-col items-center justify-center p-8 text-center max-w-2xl mx-auto">
            <div className="w-16 h-16 rounded-full bg-white flex items-center justify-center mb-6 shadow-xl">
              <Bot className="text-black" size={32} />
            </div>
            <h1 className="text-2xl md:text-3xl font-semibold text-gray-100 mb-4">
              How can I help you today?
            </h1>
            <p className="text-gray-400">
              I’m LocalOps. Describe the operational symptom, affected service, site, or asset.
            </p>
          </div>
        ) : (
          <div className="flex flex-col">
            {messages.map((msg, i) => {
              // Skip the initial greeting if we have history
              if (i === 0 && msg.role === 'assistant' && msg.content.includes('I’m LocalOps')) return null;
              return <ChatMessage key={msg.id} message={msg} />
            })}
            {isStreaming && (
              <div className="max-w-3xl w-full mx-auto px-4 py-6 flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center shrink-0">
                  <Bot size={18} className="text-white" />
                </div>
                <div className="flex space-x-1 mt-3">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#212121] via-[#212121] to-transparent pt-6 pb-6 px-4">
        {error && (
          <div className="max-w-3xl mx-auto mb-3 px-4 py-2 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg text-center">
            {error}
          </div>
        )}
        <div className="max-w-3xl mx-auto relative flex items-end bg-[#2f2f2f] rounded-2xl border border-gray-700/50 shadow-[0_0_15px_rgba(0,0,0,0.1)] focus-within:border-gray-600 transition-colors">
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe an operational issue..."
            className="w-full bg-transparent text-gray-100 placeholder-gray-400 rounded-2xl py-3.5 pl-4 pr-12 resize-none max-h-[200px] outline-none"
            rows={1}
            disabled={isStreaming}
          />
          <button
            onClick={handleSend}
            disabled={!inputText.trim() || isStreaming}
            className="absolute right-3 bottom-2.5 p-1.5 rounded-lg bg-white text-black disabled:opacity-30 disabled:bg-gray-600 transition-colors"
          >
            <ArrowUp size={20} strokeWidth={3} />
          </button>
        </div>
        <div className="text-center mt-3">
          <span className="text-xs text-gray-500">Runbooks are simulated locally; policy and approval are checked before any state-changing action.</span>
        </div>
      </div>
    </div>
  );
}

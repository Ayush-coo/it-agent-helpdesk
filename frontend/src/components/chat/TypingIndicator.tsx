export default function TypingIndicator() {
  return (
    <div className="flex items-center space-x-1.5 p-4 max-w-max bg-panel border border-panel-border rounded-2xl rounded-tl-sm mt-4">
      <div className="w-2 h-2 bg-armin rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
      <div className="w-2 h-2 bg-armin rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
      <div className="w-2 h-2 bg-armin rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
    </div>
  );
}

import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Bot, User } from 'lucide-react';
import { ChatMessage } from '../services/api';
import { apiService } from '../services/api';
import { useModel } from '../contexts/ModelContext';

const ChatInterface: React.FC = () => {
  const { activeModel, isModelLoading, setIsModelLoading } = useModel();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isModelLoading) return;

    const userMessage: ChatMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsModelLoading(true);
    setError(null);

    try {
      const response = await apiService.chatCompletion({
        messages: [...messages, userMessage],
        model: activeModel,
      });

      setMessages((prev) => [...prev, response.message]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get response');
      console.error(err);
    } finally {
      setIsModelLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full glass-card overflow-hidden rounded-xl">
      {/* Chat header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-full bg-primary/20">
            <Bot className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="font-medium">AI Assistant</h3>
            <p className="text-xs text-muted-foreground">
              Using {activeModel === 'gemma' ? 'Gemma 3 (Local)' : 'Gemini (Cloud)'} model
            </p>
          </div>
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <Bot className="w-12 h-12 mb-4 text-muted-foreground/50" />
            <p className="text-center">
              Start a conversation with the AI assistant.<br />
              Ask questions about candidates, job descriptions, or get help with recruiting tasks.
            </p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 ${
                message.role === 'assistant' ? 'items-start' : 'items-start justify-end'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-primary" />
                </div>
              )}
              <div
                className={`rounded-lg p-3 max-w-[80%] ${
                  message.role === 'assistant'
                    ? 'bg-muted/50 text-foreground'
                    : 'bg-primary/20 text-foreground ml-auto'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-secondary/20 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-secondary" />
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error message */}
      {error && (
        <div className="mx-4 mb-2 p-3 bg-destructive/10 text-destructive text-sm rounded-lg">
          <p>{error}</p>
        </div>
      )}

      {/* Chat input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-white/10">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="w-full px-4 py-3 pr-12 bg-muted/50 rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
            disabled={isModelLoading}
          />
          <button
            type="submit"
            className="absolute right-1 top-1/2 -translate-y-1/2 p-2 rounded-md bg-primary/90 hover:bg-primary text-white disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!input.trim() || isModelLoading}
          >
            {isModelLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface; 
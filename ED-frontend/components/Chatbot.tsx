"use client";

import { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send, Minimize2, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{role: 'user'|'ai', content: string}[]>([
    { role: 'ai', content: 'Hello! I am CarePath AI. How can I help you navigate the dashboard today?' }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput("");
    setIsLoading(true);

    try {
      // Send request to backend
      const res = await fetch("http://localhost:8001/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg, context: window.location.pathname })
      });
      
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'ai', content: data.reply || "Sorry, I couldn't process that." }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', content: "Error connecting to the AI assistant." }]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 p-4 bg-teal-600 text-white rounded-full shadow-lg hover:bg-teal-700 transition hover:scale-105 z-50 flex items-center justify-center"
      >
        <MessageSquare className="size-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-80 md:w-96 bg-white border border-slate-200 rounded-xl shadow-2xl flex flex-col z-50 overflow-hidden" style={{ height: '500px', maxHeight: '80vh' }}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-slate-50">
        <div className="flex items-center gap-2">
          <div className="size-8 rounded-full bg-teal-100 flex items-center justify-center text-teal-700">
            <MessageSquare className="size-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">CarePath Assistant</h3>
            <p className="text-[10px] text-slate-500">Navigation & Support</p>
          </div>
        </div>
        <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-slate-600">
          <X className="size-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${msg.role === 'user' ? 'bg-teal-600 text-white rounded-br-sm' : 'bg-white border border-slate-200 text-slate-700 rounded-bl-sm shadow-sm'}`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-white border border-slate-200 rounded-bl-sm shadow-sm flex gap-1 items-center">
              <div className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce"></div>
              <div className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
              <div className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-slate-100 bg-white">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-full px-4 py-2 focus-within:border-teal-400 focus-within:ring-1 focus-within:ring-teal-400 transition"
        >
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about the dashboard..."
            className="flex-1 bg-transparent border-none focus:outline-none text-sm text-slate-700 placeholder:text-slate-400"
          />
          <button 
            type="submit" 
            disabled={!input.trim() || isLoading}
            className="text-teal-600 hover:text-teal-700 disabled:opacity-50 transition"
          >
            <Send className="size-4" />
          </button>
        </form>
        <p className="text-center mt-2 text-[9px] text-slate-400">
          AI may generate inaccurate information. PHI is strictly blocked.
        </p>
      </div>
    </div>
  );
}

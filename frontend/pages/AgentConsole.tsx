import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User, Cpu, Sparkles, ArrowRight, RotateCcw } from 'lucide-react';
import { sendAgentMessage } from '../services/api';
import { ChatMessage, AgentResponse } from '../types';

const AgentConsole: React.FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response: AgentResponse = await sendAgentMessage(userMsg.content);
      
      const agentMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.result.answer,
        timestamp: new Date(),
        metadata: {
          intent: response.intent,
          action: response.action_taken,
          sources: response.result.sources,
          confidence: response.result.confidence
        }
      };
      
      setMessages(prev => [...prev, agentMsg]);
    } catch (error) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I encountered an error connecting to the URWA Brain core. Please check the backend connection.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-10">
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
                <div className="bg-indigo-500/20 p-2 rounded-lg">
                    <Sparkles className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                    <h2 className="text-lg font-semibold text-white">Unified Agent</h2>
                    <p className="text-xs text-slate-400">Orchestrator v3.0 • Auto-Strategy Selection</p>
                </div>
            </div>
            <button 
                onClick={() => setMessages([])}
                className="text-slate-400 hover:text-white transition-colors p-2 rounded-md hover:bg-slate-800"
                title="Clear Chat"
            >
                <RotateCcw className="w-4 h-4" />
            </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4 opacity-50">
            <Bot className="w-16 h-16 mb-4" />
            <p className="text-lg font-medium">How can URWA help you today?</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm max-w-lg w-full">
              <button onClick={() => setInput("What is the market impact of Bitcoin today?")} className="p-3 bg-slate-800 rounded-lg hover:bg-slate-700 text-left border border-slate-700">Research Bitcoin market</button>
              <button onClick={() => setInput("Extract stories from ycombinator.com")} className="p-3 bg-slate-800 rounded-lg hover:bg-slate-700 text-left border border-slate-700">Scrape Hacker News</button>
              <button onClick={() => setInput("Fact check: Python is the most popular language")} className="p-3 bg-slate-800 rounded-lg hover:bg-slate-700 text-left border border-slate-700">Fact check Python popularity</button>
              <button onClick={() => setInput("Can I scrape linkedin.com?")} className="p-3 bg-slate-800 rounded-lg hover:bg-slate-700 text-left border border-slate-700">Profile LinkedIn Protection</button>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-blue-600 flex-shrink-0 flex items-center justify-center mt-1">
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}

            <div className={`max-w-3xl rounded-2xl p-5 ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white rounded-tr-none' 
                : 'bg-surface border border-slate-700 text-slate-200 rounded-tl-none'
            }`}>
              
              {/* Agent Metadata Display */}
              {msg.role === 'assistant' && msg.metadata && (
                <div className="mb-4 flex flex-wrap gap-2 pb-3 border-b border-slate-700/50">
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-slate-700 text-slate-300 capitalize">
                    <Cpu className="w-3 h-3" />
                    {msg.metadata.intent}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <Sparkles className="w-3 h-3" />
                    {msg.metadata.action}
                  </span>
                  {msg.metadata.confidence && (
                     <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                     {(msg.metadata.confidence * 100).toFixed(0)}% Confidence
                   </span>
                  )}
                </div>
              )}

              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>

              {/* Citations / Sources */}
              {msg.metadata?.sources && msg.metadata.sources.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-700/50">
                  <p className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wide">Sources</p>
                  <div className="grid gap-2">
                    {msg.metadata.sources.map((source, idx) => (
                      <a 
                        key={idx} 
                        href={source.url} 
                        target="_blank" 
                        rel="noreferrer"
                        className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 truncate"
                      >
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
                        {source.title}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-slate-700 flex-shrink-0 flex items-center justify-center mt-1">
                <User className="w-5 h-5 text-slate-300" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
            <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex-shrink-0 flex items-center justify-center mt-1 animate-pulse">
                    <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="bg-surface border border-slate-700 rounded-2xl rounded-tl-none p-4 flex items-center gap-3">
                    <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-slate-400 font-medium animate-pulse">Analyzing & Scraping...</span>
                </div>
            </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-800 bg-slate-900">
        <div className="max-w-4xl mx-auto relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything... (e.g. 'Scrape cnn.com' or 'Research AI trends')"
            className="w-full bg-surface text-white placeholder-slate-500 border border-slate-700 rounded-xl pl-4 pr-12 py-3.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none shadow-xl"
            rows={1}
            style={{ minHeight: '52px' }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="absolute right-2 top-2 p-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-all"
          >
            {isLoading ? <Cpu className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
          </button>
        </div>
        <div className="text-center mt-2">
            <p className="text-[10px] text-slate-500">URWA Brain may produce inaccurate information. Verify important sources.</p>
        </div>
      </div>
    </div>
  );
};

export default AgentConsole;
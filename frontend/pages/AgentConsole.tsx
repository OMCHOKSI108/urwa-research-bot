import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Send,
  Bot,
  User,
  Sparkles,
  RotateCcw,
  ExternalLink,
  Copy,
  Check,
  Loader2,
  AlertCircle,
  Search,
  Globe,
  Zap,
  FileText,
  Activity,
  CheckCircle2,
  Brain,
  Wifi,
  Database,
  Hand,
  Rocket,
  Smile,
  Shield,
  BarChart3,
  Lightbulb,
  HelpCircle,
  Square
} from 'lucide-react';
import { sendAgentMessage, clearAgentHistory } from '../services/api';
import { ChatMessage, AgentResponse } from '../types';
import { useToast } from '../components/Toast';

/* ═══════════════════════════════════════════════════════════════════════════
   GREETING DETECTION - Handle casual conversation locally
   ═══════════════════════════════════════════════════════════════════════════ */
const GREETING_PATTERNS = [
  /^(hi+|hey+|hello+|hola|howdy|sup|yo)[\s!?.]*$/i,
  /^(good\s*(morning|afternoon|evening|night))[\s!?.]*$/i,
  /^(what'?s?\s*up|how\s*(are\s*you|r\s*u|is\s*it\s*going))[\s!?.]*$/i,
  /^(greetings|salutations)[\s!?.]*$/i,
  /^h+e+l+o+[\s!?.]*$/i, // Catches "hellooo", "heeellooo", etc.
  /^h+i+[\s!?.]*$/i, // Catches "hiiii", "hiii", etc.
  /^h+e+y+[\s!?.]*$/i, // Catches "heyyy", "heyyyy", etc.
];

const GREETING_RESPONSES = [
  "Hey there! I'm URWA Brain, your AI-powered web intelligence assistant. I can help you with:\n\n• **Research** - Deep dive into any topic with AI synthesis\n• **Web Scraping** - Extract data from any website\n• **Site Analysis** - Check protection levels and strategies\n• **Fact Checking** - Verify information across sources\n\nWhat would you like to explore today?",
  "Hello! Great to see you! I'm ready to help with web research, scraping, and data analysis. Just tell me what you need - whether it's researching a topic, scraping a website, or analyzing web content!",
  "Hi there! Welcome to URWA Brain! I'm your AI web intelligence companion. Ask me to research topics, scrape websites, or analyze any URL. What's on your mind?",
  "Hey! I'm here to help! Whether you need to:\n\n→ Research a topic in depth\n→ Scrape data from websites\n→ Analyze site protections\n→ Synthesize information\n\nJust ask and I'll get started!",
];

const HELP_PATTERNS = [
  /^(help|what\s*can\s*you\s*do|commands|features)[\s!?.]*$/i,
  /^(how\s*do\s*(i|you)\s*use\s*(this|you))[\s!?.]*$/i,
  /^(what\s*are\s*you|who\s*are\s*you)[\s!?.]*$/i,
  /^what\s*features?\s*(do\s*)?(you\s*)?(have|got)[\s!?.]*$/i, // "what features you have"
  /^(show|tell|list)\s*(me\s*)?(your\s*)?(features|capabilities|abilities)[\s!?.]*$/i,
];

const HELP_RESPONSE = `# URWA Brain - Your Intelligent Web Assistant

Welcome! I'm a powerful AI-powered platform for web intelligence. Here's everything I can do:

---

## 🔍 **Research & Analysis**
Deep dive into any topic with AI-powered synthesis:
- *"Research AI trends in 2026"*
- *"What are the latest developments in quantum computing?"*
- *"Find information about climate change solutions"*

I search multiple sources, analyze content, and synthesize comprehensive reports.

---

## 🌐 **Web Scraping**
Extract data from any website using intelligent strategies:
- *"Scrape news.ycombinator.com"*
- *"Extract articles from techcrunch.com"*
- *"Get product data from amazon.com/product-url"*

I automatically detect protection levels and choose the best scraping strategy (Lightweight, Stealth, or Ultra Stealth).

---

## 🛡️ **Site Analysis**
Analyze website protection and scraping feasibility:
- *"Analyze linkedin.com security"*
- *"What protection does twitter.com use?"*
- *"Can I scrape facebook.com?"*

Get detailed reports on anti-bot measures, rate limits, and recommended approaches.

---

## ✅ **Fact Checking**
Verify claims and cross-reference information:
- *"Fact check: Is this claim true?"*
- *"Verify information about X"*

I cross-reference multiple sources to provide confidence scores.

---

## 💡 **Quick Tips**
- Just type naturally - I understand intent!
- Use the quick action buttons below for common tasks
- Check **History** to see past conversations
- Visit **Settings** to configure your LLM preferences

---

*Ready to get started? Just type your request below!*`;


function isGreeting(text: string): boolean {
  const trimmed = text.trim();
  return GREETING_PATTERNS.some(pattern => pattern.test(trimmed));
}

function isHelpRequest(text: string): boolean {
  const trimmed = text.trim();
  return HELP_PATTERNS.some(pattern => pattern.test(trimmed));
}

function getGreetingResponse(): string {
  return GREETING_RESPONSES[Math.floor(Math.random() * GREETING_RESPONSES.length)];
}

/* ═══════════════════════════════════════════════════════════════════════════
   COMPACT LIVE ACTIVITY - Perplexity-style URL ticker
   ═══════════════════════════════════════════════════════════════════════════ */
interface LiveActivityFeedProps {
  isActive: boolean;
  query: string;
}

const SEARCH_SOURCES = [
  'google.com/search',
  'duckduckgo.com',
  'wikipedia.org',
  'github.com',
  'reddit.com/r/',
  'stackoverflow.com',
  'news.ycombinator.com',
  'arxiv.org',
  'medium.com',
  'techcrunch.com',
];

const LiveActivityFeed: React.FC<LiveActivityFeedProps> = ({ isActive, query }) => {
  const [currentUrl, setCurrentUrl] = useState<string>('');
  const [phase, setPhase] = useState<string>('Analyzing');
  const [urlHistory, setUrlHistory] = useState<string[]>([]);

  useEffect(() => {
    if (!isActive) {
      setCurrentUrl('');
      setPhase('Analyzing');
      setUrlHistory([]);
      return;
    }

    // Phase progression
    const phases = ['Analyzing query', 'Searching sources', 'Reading pages', 'Extracting data', 'Synthesizing'];
    let phaseIdx = 0;
    const phaseInterval = setInterval(() => {
      phaseIdx = Math.min(phaseIdx + 1, phases.length - 1);
      setPhase(phases[phaseIdx]);
    }, 1500);

    // Fast URL ticker - changes every 400ms for speed effect
    let urlIdx = 0;
    const urlInterval = setInterval(() => {
      const newUrl = SEARCH_SOURCES[urlIdx % SEARCH_SOURCES.length];
      setCurrentUrl(newUrl);
      setUrlHistory(prev => [...prev.slice(-2), newUrl]);
      urlIdx++;
    }, 400);

    return () => {
      clearInterval(phaseInterval);
      clearInterval(urlInterval);
    };
  }, [isActive, query]);

  if (!isActive) return null;

  return (
    <div
      className="mb-4 rounded-xl overflow-hidden animate-fade-up"
      style={{
        background: 'linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-muted) 100%)',
        border: '1px solid var(--border-light)',
      }}
    >
      {/* Compact Header */}
      <div
        className="flex items-center gap-2 px-3 py-2"
        style={{ borderBottom: '1px solid var(--border-light)' }}
      >
        <div className="relative">
          <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--primary)' }} />
        </div>
        <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
          {phase}
        </span>
        <div className="ml-auto flex items-center gap-1">
          <span
            className="w-1.5 h-1.5 rounded-full animate-pulse"
            style={{ background: 'var(--success)' }}
          />
          <span className="text-xs font-medium" style={{ color: 'var(--success)' }}>
            Live
          </span>
        </div>
      </div>

      {/* Fast URL Ticker */}
      <div className="px-3 py-2 flex items-center gap-2 overflow-hidden">
        <Globe className="w-3.5 h-3.5 shrink-0" style={{ color: 'var(--text-muted)' }} />
        <div className="flex-1 overflow-hidden">
          <div
            className="text-xs font-mono truncate transition-all duration-200"
            style={{ color: 'var(--primary)' }}
            key={currentUrl}
          >
            {currentUrl}
          </div>
        </div>
        <span
          className="text-xs shrink-0 px-1.5 py-0.5 rounded"
          style={{ background: 'var(--primary-bg)', color: 'var(--primary)' }}
        >
          {urlHistory.length} sources
        </span>
      </div>

      {/* Animated Progress */}
      <div className="h-0.5 relative overflow-hidden" style={{ background: 'var(--bg-muted)' }}>
        <div
          className="absolute inset-0 animate-gradient"
          style={{
            background: 'linear-gradient(90deg, var(--primary), var(--accent), var(--primary))',
            backgroundSize: '200% 100%',
          }}
        />
      </div>
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════════════════════
   TYPING INDICATOR
   ═══════════════════════════════════════════════════════════════════════════ */
const TypingIndicator: React.FC = () => (
  <div className="flex items-center gap-3">
    <div
      className="w-9 h-9 rounded-full flex items-center justify-center"
      style={{ background: 'var(--primary-bg)' }}
    >
      <Bot className="w-5 h-5" style={{ color: 'var(--primary)' }} />
    </div>

    <div
      className="px-4 py-3 rounded-2xl rounded-tl-none"
      style={{ background: 'var(--bg-muted)' }}
    >
      <div className="flex items-center gap-2">
        <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--primary)' }} />
        <span
          className="text-sm"
          style={{ color: 'var(--text-muted)' }}
        >
          Thinking...
        </span>
      </div>
    </div>
  </div>
);

/* ═══════════════════════════════════════════════════════════════════════════
   SUGGESTION CHIP
   ═══════════════════════════════════════════════════════════════════════════ */
interface SuggestionChipProps {
  text: string;
  icon: React.ElementType;
  onClick: () => void;
}

const SuggestionChip: React.FC<SuggestionChipProps> = ({ text, icon: Icon, onClick }) => (
  <button
    onClick={onClick}
    className="flex items-center gap-2 px-4 py-3 rounded-xl transition-all hover:shadow-md"
    style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-light)',
    }}
  >
    <Icon className="w-4 h-4" style={{ color: 'var(--primary)' }} />
    <span
      className="text-sm font-medium"
      style={{ color: 'var(--text-secondary)' }}
    >
      {text}
    </span>
  </button>
);

/* ═══════════════════════════════════════════════════════════════════════════
   MESSAGE BUBBLE - Modern ChatGPT-style design
   ═══════════════════════════════════════════════════════════════════════════ */
interface MessageBubbleProps {
  message: ChatMessage;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const isError = message.status === 'error';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="group py-5 px-4 transition-colors"
      style={{
        background: isUser ? 'transparent' : 'var(--bg-muted)',
      }}
    >
      <div className="max-w-3xl mx-auto flex gap-4">
        {/* Avatar */}
        <div
          className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center shadow-sm"
          style={{
            background: isUser
              ? 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)'
              : isError
                ? 'var(--error-bg)'
                : 'linear-gradient(135deg, var(--accent) 0%, #059669 100%)',
          }}
        >
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : isError ? (
            <AlertCircle className="w-4 h-4" style={{ color: 'var(--error)' }} />
          ) : (
            <Sparkles className="w-4 h-4 text-white" />
          )}
        </div>

        {/* Content Area */}
        <div className="flex-1 min-w-0">
          {/* Role Label */}
          <div className="flex items-center gap-2 mb-1.5">
            <span
              className="text-sm font-semibold"
              style={{ color: 'var(--text-primary)' }}
            >
              {isUser ? 'You' : 'URWA Brain'}
            </span>
            <span
              className="text-xs"
              style={{ color: 'var(--text-muted)' }}
            >
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>

          {/* Metadata Tags */}
          {!isUser && message.metadata && !isError && (
            <div className="flex flex-wrap gap-1.5 mb-2">
              {message.metadata.intent && (
                <span
                  className="text-xs px-2 py-0.5 rounded-full font-medium"
                  style={{ background: 'var(--primary-bg)', color: 'var(--primary)' }}
                >
                  {message.metadata.intent}
                </span>
              )}
              {message.metadata.action && (
                <span
                  className="text-xs px-2 py-0.5 rounded-full font-medium"
                  style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}
                >
                  {message.metadata.action}
                </span>
              )}
              {message.metadata.confidence && (
                <span
                  className="text-xs px-2 py-0.5 rounded-full font-medium"
                  style={{ background: 'var(--success-bg)', color: 'var(--success)' }}
                >
                  {(message.metadata.confidence * 100).toFixed(0)}% confidence
                </span>
              )}
              {message.metadata.executionTime && (
                <span
                  className="text-xs px-2 py-0.5 rounded-full font-medium"
                  style={{ background: 'var(--warning-bg)', color: 'var(--warning)' }}
                >
                  {message.metadata.executionTime.toFixed(2)}s
                </span>
              )}
            </div>
          )}

          {/* Message Content */}
          <div
            className="prose prose-sm max-w-none"
            style={{
              color: isError ? 'var(--error)' : 'var(--text-primary)',
            }}
          >
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>

          {/* Sources */}
          {!isUser && message.metadata?.sources && message.metadata.sources.length > 0 && (
            <div
              className="mt-4 p-3 rounded-lg"
              style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-light)' }}
            >
              <p
                className="text-xs font-semibold uppercase mb-2 flex items-center gap-1.5"
                style={{ color: 'var(--text-muted)' }}
              >
                <ExternalLink className="w-3 h-3" />
                Sources
              </p>
              <div className="space-y-1.5">
                {message.metadata.sources.map((source, idx) => (
                  <a
                    key={idx}
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-2 text-sm hover:underline transition-colors"
                    style={{ color: 'var(--primary)' }}
                  >
                    <span
                      className="w-5 h-5 rounded flex items-center justify-center text-xs font-medium"
                      style={{ background: 'var(--primary-bg)', color: 'var(--primary)' }}
                    >
                      {idx + 1}
                    </span>
                    <span className="truncate">{source.title}</span>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Actions - Visible on hover */}
          {!isUser && !isError && (
            <div className="mt-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleCopy}
                className="p-1.5 rounded-md transition-all hover:bg-white/50"
                title="Copy response"
              >
                {copied ? (
                  <Check className="w-4 h-4" style={{ color: 'var(--success)' }} />
                ) : (
                  <Copy className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════════════════════
   CHAT HISTORY STORAGE
   ═══════════════════════════════════════════════════════════════════════════ */
const CHAT_STORAGE_KEY = 'urwa_chat_history';

function loadChatHistory(): ChatMessage[] {
  try {
    const saved = localStorage.getItem(CHAT_STORAGE_KEY);
    if (saved) {
      const messages = JSON.parse(saved);
      // Convert timestamp strings back to Date objects
      return messages.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      }));
    }
  } catch (e) {
    console.error('Failed to load chat history:', e);
  }
  return [];
}

function saveChatHistory(messages: ChatMessage[]): void {
  try {
    // Only save the last 50 messages to avoid localStorage limits
    const toSave = messages.slice(-50);
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(toSave));
  } catch (e) {
    console.error('Failed to save chat history:', e);
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN AGENT CONSOLE
   ═══════════════════════════════════════════════════════════════════════════ */
const AgentConsole: React.FC = () => {
  const toast = useToast();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadChatHistory());
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Scroll to bottom when messages change
  useEffect(scrollToBottom, [messages]);

  // Save chat history when messages change
  useEffect(() => {
    if (messages.length > 0) {
      saveChatHistory(messages);
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userInput = input.trim();
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: userInput,
      timestamp: new Date(),
      status: 'success'
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setCurrentQuery(userInput);

    // Check for greetings (handle locally)
    if (isGreeting(userInput)) {
      const greetingMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getGreetingResponse(),
        timestamp: new Date(),
        status: 'success',
        metadata: {
          intent: 'greeting',
          action: 'local_response',
        }
      };

      // Slight delay for natural feel
      setTimeout(() => {
        setMessages(prev => [...prev, greetingMsg]);
        setCurrentQuery('');
      }, 500);
      return;
    }

    // Check for help requests (handle locally)
    if (isHelpRequest(userInput)) {
      const helpMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: HELP_RESPONSE,
        timestamp: new Date(),
        status: 'success',
        metadata: {
          intent: 'help',
          action: 'local_response',
        }
      };

      setTimeout(() => {
        setMessages(prev => [...prev, helpMsg]);
        setCurrentQuery('');
      }, 500);
      return;
    }

    // Call API for actual queries
    setIsLoading(true);

    try {
      const response = await sendAgentMessage(userInput, false);

      if (response.success && response.data) {
        const agentMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.result.answer,
          timestamp: new Date(),
          status: 'success',
          metadata: {
            intent: response.data.intent,
            action: response.data.action_taken,
            sources: response.data.result.sources,
            confidence: response.data.result.confidence,
            executionTime: response.data.execution_time,
            llmUsed: response.data.llm_used
          }
        };
        setMessages(prev => [...prev, agentMsg]);
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: error instanceof Error ? error.message : 'An error occurred. Please try again.',
        timestamp: new Date(),
        status: 'error'
      };
      setMessages(prev => [...prev, errorMsg]);
      toast.error('Request Failed', error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setIsLoading(false);
      setCurrentQuery('');
      inputRef.current?.focus();
    }
  };

  const handleClearChat = async () => {
    try {
      await clearAgentHistory();
      setMessages([]);
      localStorage.removeItem(CHAT_STORAGE_KEY); // Clear saved history
      toast.success('Chat Cleared', 'Conversation history has been reset');
    } catch (error) {
      toast.error('Clear Failed', 'Could not clear conversation');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    { text: "Research AI trends in 2026", icon: Search },
    { text: "Scrape news.ycombinator.com", icon: Globe },
    { text: "Analyze linkedin.com security", icon: Zap },
    { text: "Summarize recent tech news", icon: FileText },
  ];

  return (
    <div
      className="flex flex-col h-full"
      style={{ background: 'var(--bg-base)' }}
    >
      {/* Header */}
      <header
        className="px-6 py-4 flex items-center justify-between"
        style={{
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-light)',
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="p-2 rounded-lg"
            style={{ background: 'var(--primary-bg)' }}
          >
            <Bot className="w-5 h-5" style={{ color: 'var(--primary)' }} />
          </div>
          <div>
            <h2
              className="font-semibold"
              style={{ color: 'var(--text-primary)' }}
            >
              AI Agent
            </h2>
            <p
              className="text-xs"
              style={{ color: 'var(--text-muted)' }}
            >
              Unified web intelligence • Say hi or ask anything!
            </p>
          </div>
        </div>

        <button
          onClick={handleClearChat}
          className="btn btn-ghost btn-sm"
        >
          <RotateCcw className="w-4 h-4" />
          Clear Chat
        </button>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6"
              style={{ background: 'var(--primary-bg)' }}
            >
              <Sparkles className="w-8 h-8" style={{ color: 'var(--primary)' }} />
            </div>

            <h3
              className="text-xl font-semibold mb-2"
              style={{ color: 'var(--text-primary)' }}
            >
              How can I help you today?
            </h3>
            <p
              className="text-sm mb-8 max-w-md"
              style={{ color: 'var(--text-muted)' }}
            >
              Say hello, ask a question, or try one of these suggestions.
              I can research topics, scrape websites, and more!
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-xl">
              {suggestions.map((suggestion, idx) => (
                <SuggestionChip
                  key={idx}
                  text={suggestion.text}
                  icon={suggestion.icon}
                  onClick={() => setInput(suggestion.text)}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Live Activity Feed */}
            {isLoading && <LiveActivityFeed isActive={isLoading} query={currentQuery} />}

            {/* Simple typing indicator as fallback */}
            {isLoading && !currentQuery && <TypingIndicator />}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Enhanced Premium Input Area */}
      <div
        className="p-5"
        style={{
          background: 'linear-gradient(to top, var(--bg-surface) 0%, var(--bg-base) 100%)',
          borderTop: '1px solid var(--border-light)',
        }}
      >
        <div className="max-w-3xl mx-auto space-y-3">
          {/* Quick Action Chips */}
          <div className="flex flex-wrap gap-2 justify-center">
            {[
              { icon: Search, label: 'Research a topic', query: 'Research ' },
              { icon: Globe, label: 'Scrape website', query: 'Scrape ' },
              { icon: Shield, label: 'Analyze site', query: 'Analyze ' },
            ].map((action) => (
              <button
                key={action.label}
                onClick={() => {
                  setInput(action.query);
                  inputRef.current?.focus();
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all hover:scale-105"
                style={{
                  background: 'var(--bg-muted)',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border-light)',
                }}
              >
                <action.icon className="w-3.5 h-3.5" />
                {action.label}
              </button>
            ))}
          </div>

          {/* Premium Input Container */}
          <div
            className="relative rounded-2xl overflow-hidden shadow-lg"
            style={{
              background: 'var(--bg-surface)',
              border: '2px solid transparent',
              backgroundClip: 'padding-box',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08), 0 0 0 1px var(--border-light)',
            }}
          >
            {/* Gradient Border Effect */}
            <div
              className="absolute inset-0 rounded-2xl -z-10"
              style={{
                background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%)',
                margin: '-2px',
                opacity: 0.15,
              }}
            />

            <div className="flex items-end gap-2 p-2">
              {/* Avatar Icon */}
              <div
                className="p-2.5 rounded-xl shrink-0 mb-0.5"
                style={{ background: 'var(--primary-bg)' }}
              >
                <Brain className="w-5 h-5" style={{ color: 'var(--primary)' }} />
              </div>

              {/* Text Input */}
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything... Research topics, scrape websites, analyze URLs"
                className="flex-1 px-3 py-3 resize-none focus:outline-none text-sm"
                style={{
                  background: 'transparent',
                  color: 'var(--text-primary)',
                  minHeight: '48px',
                  maxHeight: '150px',
                }}
                rows={1}
              />

              {/* Stop Button - visible during loading */}
              {isLoading && (
                <button
                  onClick={() => {
                    setIsLoading(false);
                    setCurrentQuery('');
                    toast.info('Stopped', 'Request cancelled');
                  }}
                  className="p-3 rounded-xl transition-all shrink-0 mb-0.5"
                  style={{
                    background: 'var(--error-bg)',
                    color: 'var(--error)',
                  }}
                  title="Stop generation"
                >
                  <Square className="w-5 h-5" fill="currentColor" />
                </button>
              )}

              {/* Send Button */}
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="p-3 rounded-xl transition-all shrink-0 mb-0.5"
                style={{
                  background: input.trim() && !isLoading
                    ? 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)'
                    : 'var(--bg-muted)',
                  color: input.trim() && !isLoading ? 'white' : 'var(--text-muted)',
                  boxShadow: input.trim() && !isLoading ? '0 2px 8px rgba(124, 58, 237, 0.3)' : 'none',
                }}
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* Helpful Hint */}
          <p
            className="text-center text-xs flex items-center justify-center gap-1.5"
            style={{ color: 'var(--text-muted)' }}
          >
            <Lightbulb className="w-3.5 h-3.5" />
            <span>Press <kbd className="px-1.5 py-0.5 rounded text-xs font-mono" style={{ background: 'var(--bg-muted)' }}>Enter</kbd> to send • <kbd className="px-1.5 py-0.5 rounded text-xs font-mono" style={{ background: 'var(--bg-muted)' }}>Shift+Enter</kbd> for new line</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AgentConsole;
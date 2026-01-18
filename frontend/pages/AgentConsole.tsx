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
  HelpCircle
} from 'lucide-react';
import { sendAgentMessage, clearAgentHistory } from '../services/api';
import { ChatMessage, AgentResponse } from '../types';
import { useToast } from '../components/Toast';

/* ═══════════════════════════════════════════════════════════════════════════
   GREETING DETECTION - Handle casual conversation locally
   ═══════════════════════════════════════════════════════════════════════════ */
const GREETING_PATTERNS = [
  /^(hi|hey|hello|hola|howdy|sup|yo)[\s!?.]*$/i,
  /^(good\s*(morning|afternoon|evening|night))[\s!?.]*$/i,
  /^(what'?s?\s*up|how\s*(are\s*you|r\s*u|is\s*it\s*going))[\s!?.]*$/i,
  /^(greetings|salutations)[\s!?.]*$/i,
  /^(hii+|heyy+|helloo+)[\s!?.]*$/i,
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
];

const HELP_RESPONSE = `# URWA Brain Capabilities

I'm an intelligent web research and scraping assistant. Here's what I can do:

## Research Mode
Ask me to research any topic:
- *"Research AI trends in 2026"*
- *"What are the latest developments in quantum computing?"*
- *"Summarize news about climate change"*

## Web Scraping
I can extract data from websites:
- *"Scrape news.ycombinator.com"*
- *"Extract articles from techcrunch.com"*
- *"Get product data from amazon.com/product-url"*

## Site Analysis
Check website protection levels:
- *"Analyze linkedin.com security"*
- *"What protection does twitter.com use?"*
- *"Can I scrape facebook.com?"*

## Fact Checking
Verify claims and information:
- *"Fact check: Is X true?"*
- *"Verify this claim about Y"*

Just type naturally and I'll understand your intent!`;

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
   ACTIVITY STEP COMPONENT - Shows individual action with animation
   ═══════════════════════════════════════════════════════════════════════════ */
interface ActivityStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'complete' | 'error';
  icon: React.ElementType;
  detail?: string;
}

const ActivityStepItem: React.FC<{ step: ActivityStep; index: number }> = ({ step, index }) => {
  const statusStyles = {
    pending: { color: 'var(--text-muted)', bg: 'var(--bg-muted)' },
    active: { color: 'var(--primary)', bg: 'var(--primary-bg)' },
    complete: { color: 'var(--success)', bg: 'var(--success-bg)' },
    error: { color: 'var(--error)', bg: 'var(--error-bg)' },
  };

  const styles = statusStyles[step.status];
  const Icon = step.icon;

  return (
    <div
      className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-300 ${step.status === 'active' ? 'animate-pulse' : ''
        }`}
      style={{
        background: step.status === 'active' ? styles.bg : 'transparent',
        animationDelay: `${index * 100}ms`,
      }}
    >
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center transition-all"
        style={{ background: styles.bg }}
      >
        {step.status === 'active' ? (
          <Loader2 className="w-4 h-4 animate-spin" style={{ color: styles.color }} />
        ) : step.status === 'complete' ? (
          <CheckCircle2 className="w-4 h-4" style={{ color: styles.color }} />
        ) : (
          <Icon className="w-4 h-4" style={{ color: styles.color }} />
        )}
      </div>

      <div className="flex-1">
        <p
          className="text-sm font-medium"
          style={{ color: step.status === 'pending' ? 'var(--text-muted)' : 'var(--text-primary)' }}
        >
          {step.label}
        </p>
        {step.detail && step.status === 'active' && (
          <p
            className="text-xs mt-0.5 animate-fade-in"
            style={{ color: 'var(--text-muted)' }}
          >
            {step.detail}
          </p>
        )}
      </div>

      {step.status === 'complete' && (
        <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--success)' }} />
      )}
    </div>
  );
};

/* ═══════════════════════════════════════════════════════════════════════════
   LIVE ACTIVITY FEED - Shows real-time agent actions
   ═══════════════════════════════════════════════════════════════════════════ */
interface LiveActivityFeedProps {
  isActive: boolean;
  query: string;
}

const LiveActivityFeed: React.FC<LiveActivityFeedProps> = ({ isActive, query }) => {
  const [steps, setSteps] = useState<ActivityStep[]>([]);
  const [currentUrl, setCurrentUrl] = useState<string>('');

  useEffect(() => {
    if (!isActive) {
      setSteps([]);
      setCurrentUrl('');
      return;
    }

    // Simulate activity steps based on query
    const isResearch = /research|find|search|what is|explain/i.test(query);
    const isScrape = /scrape|extract|get data|crawl/i.test(query);
    const isAnalyze = /analyze|check|security|protection/i.test(query);

    const baseSteps: ActivityStep[] = [
      { id: '1', label: 'Understanding your request', status: 'pending', icon: Brain },
      { id: '2', label: 'Planning execution strategy', status: 'pending', icon: Zap },
    ];

    if (isResearch) {
      baseSteps.push(
        { id: '3', label: 'Searching the web', status: 'pending', icon: Search, detail: 'Querying multiple sources...' },
        { id: '4', label: 'Analyzing sources', status: 'pending', icon: Globe, detail: '' },
        { id: '5', label: 'Synthesizing information', status: 'pending', icon: Sparkles },
      );
    } else if (isScrape) {
      baseSteps.push(
        { id: '3', label: 'Analyzing target site', status: 'pending', icon: Globe, detail: '' },
        { id: '4', label: 'Selecting scraping strategy', status: 'pending', icon: Zap },
        { id: '5', label: 'Extracting data', status: 'pending', icon: Database },
      );
    } else if (isAnalyze) {
      baseSteps.push(
        { id: '3', label: 'Probing target URL', status: 'pending', icon: Wifi },
        { id: '4', label: 'Detecting protections', status: 'pending', icon: Activity },
        { id: '5', label: 'Generating report', status: 'pending', icon: FileText },
      );
    } else {
      baseSteps.push(
        { id: '3', label: 'Processing with AI', status: 'pending', icon: Brain },
        { id: '4', label: 'Generating response', status: 'pending', icon: Sparkles },
      );
    }

    baseSteps.push({ id: 'final', label: 'Finalizing response', status: 'pending', icon: CheckCircle2 });

    setSteps(baseSteps);

    // Animate through steps
    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < baseSteps.length) {
        setSteps(prev => prev.map((step, idx) => ({
          ...step,
          status: idx < currentStep ? 'complete' : idx === currentStep ? 'active' : 'pending',
          detail: idx === currentStep && step.detail !== undefined ? getStepDetail(step, query) : step.detail,
        })));

        // Simulate discovered URLs
        if (currentStep === 2 && (isResearch || isScrape)) {
          const urls = ['google.com', 'wikipedia.org', 'github.com', 'stackexchange.com'];
          setCurrentUrl(urls[Math.floor(Math.random() * urls.length)]);
        }

        currentStep++;
      }
    }, 800);

    return () => clearInterval(interval);
  }, [isActive, query]);

  if (!isActive || steps.length === 0) return null;

  return (
    <div
      className="saas-card p-4 animate-slide-up mb-4 overflow-hidden"
      style={{ background: 'var(--bg-surface)' }}
    >
      <div className="flex items-center gap-2 mb-4">
        <div
          className="p-1.5 rounded-lg"
          style={{ background: 'var(--primary-bg)' }}
        >
          <Activity className="w-4 h-4" style={{ color: 'var(--primary)' }} />
        </div>
        <h4 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
          Live Activity
        </h4>
        <div
          className="ml-auto flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium"
          style={{ background: 'var(--success-bg)', color: 'var(--success)' }}
        >
          <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--success)' }} />
          PROCESSING
        </div>
      </div>

      {/* Current URL being accessed */}
      {currentUrl && (
        <div
          className="mb-3 px-3 py-2 rounded-lg flex items-center gap-2 animate-fade-in"
          style={{ background: 'var(--bg-muted)' }}
        >
          <Globe className="w-4 h-4" style={{ color: 'var(--primary)' }} />
          <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>
            Accessing: <span style={{ color: 'var(--primary)' }}>{currentUrl}</span>
          </span>
        </div>
      )}

      {/* Activity Steps */}
      <div className="space-y-1">
        {steps.map((step, idx) => (
          <ActivityStepItem key={step.id} step={step} index={idx} />
        ))}
      </div>

      {/* Progress Bar */}
      <div className="mt-4">
        <div
          className="h-1 rounded-full overflow-hidden"
          style={{ background: 'var(--bg-muted)' }}
        >
          <div
            className="h-full rounded-full transition-all duration-500 ease-out"
            style={{
              width: `${(steps.filter(s => s.status === 'complete').length / steps.length) * 100}%`,
              background: 'linear-gradient(90deg, var(--primary), var(--accent))',
            }}
          />
        </div>
      </div>
    </div>
  );
};

function getStepDetail(step: ActivityStep, query: string): string {
  const urls = ['news.ycombinator.com', 'reddit.com', 'twitter.com', 'medium.com'];
  const actions = [
    'Fetching page content...',
    'Parsing HTML structure...',
    'Extracting relevant data...',
    'Cross-referencing sources...',
  ];

  if (step.id === '3') return actions[0];
  if (step.id === '4') return actions[1];
  return '';
}

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
   MESSAGE BUBBLE
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
    <div className={`flex gap-3 animate-slide-up ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center"
        style={{
          background: isUser ? 'var(--primary)' : isError ? 'var(--error-bg)' : 'var(--primary-bg)',
        }}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : isError ? (
          <AlertCircle className="w-5 h-5" style={{ color: 'var(--error)' }} />
        ) : (
          <Bot className="w-5 h-5" style={{ color: 'var(--primary)' }} />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-2xl ${isUser ? 'text-right' : ''}`}>
        <div
          className={`inline-block px-4 py-3 rounded-2xl ${isUser ? 'rounded-tr-none' : 'rounded-tl-none'
            }`}
          style={{
            background: isUser ? 'var(--primary)' : isError ? 'var(--error-bg)' : 'var(--bg-muted)',
            color: isUser ? 'white' : isError ? 'var(--error)' : 'var(--text-primary)',
            textAlign: 'left',
          }}
        >
          {/* Metadata Tags */}
          {!isUser && message.metadata && !isError && (
            <div className="flex flex-wrap gap-2 mb-3">
              {message.metadata.intent && (
                <span className="badge badge-primary">
                  {message.metadata.intent}
                </span>
              )}
              {message.metadata.action && (
                <span className="badge badge-info">
                  {message.metadata.action}
                </span>
              )}
              {message.metadata.confidence && (
                <span className="badge badge-success">
                  {(message.metadata.confidence * 100).toFixed(0)}% confidence
                </span>
              )}
              {message.metadata.executionTime && (
                <span className="badge badge-warning">
                  {message.metadata.executionTime.toFixed(2)}s
                </span>
              )}
            </div>
          )}

          {/* Content */}
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>

          {/* Sources */}
          {!isUser && message.metadata?.sources && message.metadata.sources.length > 0 && (
            <div
              className="mt-3 pt-3"
              style={{ borderTop: '1px solid var(--border-light)' }}
            >
              <p
                className="text-xs font-semibold uppercase mb-2"
                style={{ color: 'var(--text-muted)' }}
              >
                Sources
              </p>
              <div className="space-y-1">
                {message.metadata.sources.map((source, idx) => (
                  <a
                    key={idx}
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-2 text-sm hover:underline"
                    style={{ color: 'var(--primary)' }}
                  >
                    <ExternalLink className="w-3 h-3" />
                    {source.title}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        {!isUser && !isError && (
          <div className="mt-2 flex gap-2">
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-md transition-all hover:bg-gray-100"
              title="Copy response"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5" style={{ color: 'var(--success)' }} />
              ) : (
                <Copy className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} />
              )}
            </button>
          </div>
        )}
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

      {/* Input Area */}
      <div
        className="p-4"
        style={{
          background: 'var(--bg-surface)',
          borderTop: '1px solid var(--border-light)',
        }}
      >
        <div className="max-w-3xl mx-auto">
          <div
            className="relative rounded-xl overflow-hidden"
            style={{
              background: 'var(--bg-muted)',
              border: '1px solid var(--border-light)',
            }}
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Say hello or ask anything... (Press Enter to send)"
              className="w-full px-4 py-3.5 pr-14 resize-none focus:outline-none"
              style={{
                background: 'transparent',
                color: 'var(--text-primary)',
                minHeight: '52px',
                maxHeight: '120px',
              }}
              rows={1}
            />

            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 rounded-lg transition-all btn-primary"
              style={{
                opacity: input.trim() && !isLoading ? 1 : 0.5,
              }}
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          <p
            className="text-center mt-3 text-xs flex items-center justify-center gap-1.5"
            style={{ color: 'var(--text-muted)' }}
          >
            <Lightbulb className="w-3.5 h-3.5" />
            Try saying "hi" or "help" to see what I can do!
          </p>
        </div>
      </div>
    </div>
  );
};

export default AgentConsole;
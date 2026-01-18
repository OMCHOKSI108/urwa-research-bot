import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    History as HistoryIcon,
    MessageSquare,
    Trash2,
    ChevronRight,
    Bot,
    User,
    Clock,
    Search,
    Calendar,
    RefreshCw,
} from 'lucide-react';
import { ChatMessage, AppRoute } from '../types';
import { useToast } from '../components/Toast';

/* ═══════════════════════════════════════════════════════════════════════════
   CHAT HISTORY PAGE - View and manage past conversations
   ═══════════════════════════════════════════════════════════════════════════ */

const CHAT_STORAGE_KEY = 'urwa_chat_history';

interface ChatSession {
    id: string;
    title: string;
    preview: string;
    messageCount: number;
    lastUpdated: Date;
    messages: ChatMessage[];
}

function loadChatHistory(): ChatMessage[] {
    try {
        const saved = localStorage.getItem(CHAT_STORAGE_KEY);
        if (saved) {
            const messages = JSON.parse(saved);
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

function groupMessagesIntSessions(messages: ChatMessage[]): ChatSession[] {
    if (messages.length === 0) return [];

    // Group by day and create sessions
    const sessions: ChatSession[] = [];
    let currentSession: ChatMessage[] = [];
    let lastDate: string | null = null;

    messages.forEach((msg, idx) => {
        const msgDate = new Date(msg.timestamp).toDateString();

        // Start new session if: first message, or 30+ min gap, or different day
        const prevMsg = messages[idx - 1];
        const timeDiff = prevMsg
            ? (new Date(msg.timestamp).getTime() - new Date(prevMsg.timestamp).getTime()) / 1000 / 60
            : 0;

        if (!lastDate || msgDate !== lastDate || timeDiff > 30) {
            if (currentSession.length > 0) {
                const userMsgs = currentSession.filter(m => m.role === 'user');
                const firstUserMsg = userMsgs[0]?.content || 'Conversation';
                sessions.push({
                    id: currentSession[0].id,
                    title: firstUserMsg.slice(0, 50) + (firstUserMsg.length > 50 ? '...' : ''),
                    preview: currentSession[currentSession.length - 1]?.content?.slice(0, 100) || '',
                    messageCount: currentSession.length,
                    lastUpdated: new Date(currentSession[currentSession.length - 1].timestamp),
                    messages: [...currentSession],
                });
            }
            currentSession = [msg];
            lastDate = msgDate;
        } else {
            currentSession.push(msg);
        }
    });

    // Don't forget the last session
    if (currentSession.length > 0) {
        const userMsgs = currentSession.filter(m => m.role === 'user');
        const firstUserMsg = userMsgs[0]?.content || 'Conversation';
        sessions.push({
            id: currentSession[0].id,
            title: firstUserMsg.slice(0, 50) + (firstUserMsg.length > 50 ? '...' : ''),
            preview: currentSession[currentSession.length - 1]?.content?.slice(0, 100) || '',
            messageCount: currentSession.length,
            lastUpdated: new Date(currentSession[currentSession.length - 1].timestamp),
            messages: [...currentSession],
        });
    }

    return sessions.reverse(); // Most recent first
}

const History: React.FC = () => {
    const navigate = useNavigate();
    const toast = useToast();
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const messages = loadChatHistory();
        const grouped = groupMessagesIntSessions(messages);
        setSessions(grouped);
        setIsLoading(false);
    }, []);

    const handleClearAll = () => {
        if (window.confirm('Are you sure you want to clear all chat history? This cannot be undone.')) {
            localStorage.removeItem(CHAT_STORAGE_KEY);
            setSessions([]);
            toast.success('Cleared', 'All chat history has been deleted');
        }
    };

    const handleGoToChat = () => {
        navigate(AppRoute.AGENT);
    };

    const filteredSessions = sessions.filter(session =>
        session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        session.preview.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const formatDate = (date: Date) => {
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) return 'Today';
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        return date.toLocaleDateString();
    };

    return (
        <div
            className="h-full overflow-y-auto"
            style={{ background: 'var(--bg-base)' }}
        >
            <div className="p-8 max-w-4xl mx-auto">
                {/* Header */}
                <header className="flex justify-between items-start mb-8">
                    <div>
                        <h1
                            className="text-2xl font-bold font-display mb-1 flex items-center gap-3"
                            style={{ color: 'var(--text-primary)' }}
                        >
                            <div
                                className="p-2 rounded-lg"
                                style={{ background: 'var(--primary-bg)' }}
                            >
                                <HistoryIcon className="w-6 h-6" style={{ color: 'var(--primary)' }} />
                            </div>
                            Chat History
                        </h1>
                        <p style={{ color: 'var(--text-muted)' }}>
                            View and manage your past conversations
                        </p>
                    </div>

                    <div className="flex gap-2">
                        <button onClick={handleGoToChat} className="btn btn-primary btn-sm">
                            <MessageSquare className="w-4 h-4" />
                            New Chat
                        </button>
                        {sessions.length > 0 && (
                            <button onClick={handleClearAll} className="btn btn-secondary btn-sm">
                                <Trash2 className="w-4 h-4" />
                                Clear All
                            </button>
                        )}
                    </div>
                </header>

                {/* Search */}
                {sessions.length > 0 && (
                    <div className="mb-6">
                        <div
                            className="flex items-center gap-2 px-4 py-3 rounded-xl"
                            style={{ background: 'var(--bg-muted)', border: '1px solid var(--border-light)' }}
                        >
                            <Search className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
                            <input
                                type="text"
                                placeholder="Search conversations..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="flex-1 bg-transparent border-none outline-none text-sm"
                                style={{ color: 'var(--text-primary)' }}
                            />
                        </div>
                    </div>
                )}

                {/* Loading */}
                {isLoading && (
                    <div className="flex items-center justify-center py-12">
                        <RefreshCw className="w-6 h-6 animate-spin" style={{ color: 'var(--primary)' }} />
                    </div>
                )}

                {/* Empty State */}
                {!isLoading && sessions.length === 0 && (
                    <div
                        className="saas-card p-12 text-center"
                    >
                        <div
                            className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center"
                            style={{ background: 'var(--primary-bg)' }}
                        >
                            <MessageSquare className="w-8 h-8" style={{ color: 'var(--primary)' }} />
                        </div>
                        <h2
                            className="text-lg font-semibold mb-2"
                            style={{ color: 'var(--text-primary)' }}
                        >
                            No conversations yet
                        </h2>
                        <p
                            className="text-sm mb-6"
                            style={{ color: 'var(--text-muted)' }}
                        >
                            Start chatting with the AI Agent to see your history here
                        </p>
                        <button onClick={handleGoToChat} className="btn btn-primary">
                            <Bot className="w-4 h-4" />
                            Start Chatting
                        </button>
                    </div>
                )}

                {/* Session List */}
                {!isLoading && filteredSessions.length > 0 && (
                    <div className="space-y-3">
                        {filteredSessions.map((session) => (
                            <div
                                key={session.id}
                                onClick={handleGoToChat}
                                className="saas-card p-4 cursor-pointer group hover:shadow-md transition-all"
                            >
                                <div className="flex items-start gap-4">
                                    <div
                                        className="p-2.5 rounded-xl shrink-0"
                                        style={{ background: 'var(--primary-bg)' }}
                                    >
                                        <Bot className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3
                                                className="font-medium truncate"
                                                style={{ color: 'var(--text-primary)' }}
                                            >
                                                {session.title}
                                            </h3>
                                            <span
                                                className="text-xs px-2 py-0.5 rounded-full shrink-0"
                                                style={{ background: 'var(--bg-muted)', color: 'var(--text-muted)' }}
                                            >
                                                {session.messageCount} messages
                                            </span>
                                        </div>

                                        <p
                                            className="text-sm truncate mb-2"
                                            style={{ color: 'var(--text-muted)' }}
                                        >
                                            {session.preview}
                                        </p>

                                        <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--text-muted)' }}>
                                            <span className="flex items-center gap-1">
                                                <Calendar className="w-3 h-3" />
                                                {formatDate(session.lastUpdated)}
                                            </span>
                                            <span className="flex items-center gap-1">
                                                <Clock className="w-3 h-3" />
                                                {session.lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </div>
                                    </div>

                                    <ChevronRight
                                        className="w-5 h-5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                        style={{ color: 'var(--text-muted)' }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* No results */}
                {!isLoading && sessions.length > 0 && filteredSessions.length === 0 && (
                    <div className="text-center py-12">
                        <Search className="w-8 h-8 mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
                        <p style={{ color: 'var(--text-muted)' }}>
                            No conversations found matching "{searchQuery}"
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default History;

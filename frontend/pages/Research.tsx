import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import {
    Search,
    Loader2,
    ExternalLink,
    Clock,
    Zap,
    BookOpen,
    ChevronDown,
    ChevronUp,
    Copy,
    Check,
    AlertCircle,
    Sparkles,
    RefreshCw
} from 'lucide-react';
import { performResearch, ResearchResult } from '../services/api';
import { useToast } from '../components/Toast';

/* ═══════════════════════════════════════════════════════════════════════════
   SOURCE CARD COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
interface SourceCardProps {
    source: { url: string; title: string; snippet?: string };
    index: number;
}

const SourceCard: React.FC<SourceCardProps> = ({ source, index }) => (
    <a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className="saas-card p-4 group block transition-all hover:border-primary"
        style={{ borderColor: 'var(--border-light)' }}
    >
        <div className="flex items-start gap-3">
            <span
                className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold"
                style={{ background: 'var(--primary-bg)', color: 'var(--primary)' }}
            >
                {index + 1}
            </span>
            <div className="flex-1 min-w-0">
                <h4
                    className="font-medium text-sm truncate group-hover:text-primary transition-colors"
                    style={{ color: 'var(--text-primary)' }}
                >
                    {source.title}
                </h4>
                {source.snippet && (
                    <p
                        className="text-xs mt-1 line-clamp-2"
                        style={{ color: 'var(--text-muted)' }}
                    >
                        {source.snippet}
                    </p>
                )}
                <div className="flex items-center gap-1 mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                    <ExternalLink className="w-3 h-3" />
                    <span className="truncate">{new URL(source.url).hostname}</span>
                </div>
            </div>
        </div>
    </a>
);

/* ═══════════════════════════════════════════════════════════════════════════
   RESULT DISPLAY COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
interface ResultDisplayProps {
    result: ResearchResult;
    query: string;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({ result, query }) => {
    const [showAllSources, setShowAllSources] = useState(false);
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(result.answer);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const visibleSources = showAllSources ? result.sources : result.sources.slice(0, 4);

    return (
        <div className="space-y-6 animate-slide-up">
            {/* Query Badge */}
            <div className="flex items-center gap-2 flex-wrap">
                <span
                    className="text-sm font-medium px-3 py-1.5 rounded-full"
                    style={{ background: 'var(--primary-bg)', color: 'var(--primary)' }}
                >
                    Query: {query}
                </span>
                <span className="badge badge-success">
                    <Clock className="w-3 h-3" />
                    {result.research_time.toFixed(2)}s
                </span>
                <span className="badge badge-info">
                    {result.llm_used}
                </span>
                <span className="badge badge-warning">
                    {(result.confidence * 100).toFixed(0)}% confidence
                </span>
            </div>

            {/* Answer Card */}
            <div className="saas-card-elevated p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                        <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                            Research Answer
                        </h3>
                    </div>
                    <button
                        onClick={handleCopy}
                        className="btn btn-ghost btn-sm"
                    >
                        {copied ? (
                            <>
                                <Check className="w-4 h-4" style={{ color: 'var(--success)' }} />
                                Copied!
                            </>
                        ) : (
                            <>
                                <Copy className="w-4 h-4" />
                                Copy
                            </>
                        )}
                    </button>
                </div>

                <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{result.answer}</ReactMarkdown>
                </div>
            </div>

            {/* Sources Section */}
            {result.sources.length > 0 && (
                <div>
                    <h3
                        className="font-semibold mb-4 flex items-center gap-2"
                        style={{ color: 'var(--text-primary)' }}
                    >
                        <BookOpen className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                        Sources ({result.sources.length})
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {visibleSources.map((source, idx) => (
                            <SourceCard key={idx} source={source} index={idx} />
                        ))}
                    </div>

                    {result.sources.length > 4 && (
                        <button
                            onClick={() => setShowAllSources(!showAllSources)}
                            className="btn btn-ghost mt-4 w-full"
                        >
                            {showAllSources ? (
                                <>
                                    <ChevronUp className="w-4 h-4" />
                                    Show Less
                                </>
                            ) : (
                                <>
                                    <ChevronDown className="w-4 h-4" />
                                    Show {result.sources.length - 4} More Sources
                                </>
                            )}
                        </button>
                    )}
                </div>
            )}

            {/* Follow-up Questions */}
            {result.follow_up_questions.length > 0 && (
                <div>
                    <h3
                        className="font-semibold mb-4"
                        style={{ color: 'var(--text-primary)' }}
                    >
                        Related Questions
                    </h3>
                    <div className="flex flex-wrap gap-2">
                        {result.follow_up_questions.map((question, idx) => (
                            <span
                                key={idx}
                                className="px-3 py-2 rounded-lg text-sm cursor-pointer hover:shadow-sm transition-all"
                                style={{
                                    background: 'var(--bg-muted)',
                                    color: 'var(--text-secondary)',
                                    border: '1px solid var(--border-light)',
                                }}
                            >
                                {question}
                            </span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN RESEARCH PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
const Research: React.FC = () => {
    const toast = useToast();
    const [query, setQuery] = useState('');
    const [isDeepSearch, setIsDeepSearch] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<ResearchResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async () => {
        if (!query.trim() || isLoading) return;

        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await performResearch(query, isDeepSearch, false);

            if (response.success && response.data) {
                setResult(response.data);
                toast.success('Research Complete', `Found ${response.data.sources.length} sources`);
            } else {
                throw new Error(response.error || 'Research failed');
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'An error occurred';
            setError(message);
            toast.error('Research Failed', message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    };

    return (
        <div
            className="h-full overflow-y-auto"
            style={{ background: 'var(--bg-base)' }}
        >
            <div className="p-8 max-w-4xl mx-auto space-y-8">

                {/* Header */}
                <header className="text-center">
                    <div
                        className="w-14 h-14 mx-auto mb-4 rounded-2xl flex items-center justify-center"
                        style={{ background: 'var(--primary-bg)' }}
                    >
                        <Search className="w-7 h-7" style={{ color: 'var(--primary)' }} />
                    </div>
                    <h1
                        className="text-2xl font-bold font-display mb-2"
                        style={{ color: 'var(--text-primary)' }}
                    >
                        Deep Research
                    </h1>
                    <p
                        className="text-sm"
                        style={{ color: 'var(--text-muted)' }}
                    >
                        AI-powered multi-source research with intelligent synthesis
                    </p>
                </header>

                {/* Search Box */}
                <div className="saas-card-elevated p-6">
                    <div
                        className="relative rounded-xl overflow-hidden mb-4"
                        style={{
                            background: 'var(--bg-muted)',
                            border: '1px solid var(--border-light)',
                        }}
                    >
                        <div className="flex items-center px-4">
                            <Search className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="What would you like to research?"
                                className="flex-1 px-3 py-4 bg-transparent focus:outline-none"
                                style={{ color: 'var(--text-primary)' }}
                            />
                        </div>
                    </div>

                    <div className="flex items-center justify-between">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={isDeepSearch}
                                onChange={(e) => setIsDeepSearch(e.target.checked)}
                                className="w-4 h-4 rounded"
                                style={{ accentColor: 'var(--primary)' }}
                            />
                            <span
                                className="text-sm font-medium flex items-center gap-1"
                                style={{ color: 'var(--text-secondary)' }}
                            >
                                <Zap className="w-4 h-4" style={{ color: 'var(--warning)' }} />
                                Deep Search (more thorough, slower)
                            </span>
                        </label>

                        <button
                            onClick={handleSearch}
                            disabled={!query.trim() || isLoading}
                            className="btn btn-primary"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Researching...
                                </>
                            ) : (
                                <>
                                    <Search className="w-4 h-4" />
                                    Research
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Loading State */}
                {isLoading && (
                    <div className="text-center py-12">
                        <div
                            className="w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center"
                            style={{ background: 'var(--primary-bg)' }}
                        >
                            <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--primary)' }} />
                        </div>
                        <p className="font-medium" style={{ color: 'var(--text-primary)' }}>
                            Researching your query...
                        </p>
                        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                            {isDeepSearch ? 'Deep search may take 30-60 seconds' : 'This usually takes 10-20 seconds'}
                        </p>
                    </div>
                )}

                {/* Error State */}
                {error && !isLoading && (
                    <div
                        className="saas-card p-6 text-center"
                        style={{ background: 'var(--error-bg)', borderColor: 'var(--error)' }}
                    >
                        <AlertCircle className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--error)' }} />
                        <h3 className="font-semibold mb-1" style={{ color: 'var(--error)' }}>
                            Research Failed
                        </h3>
                        <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
                            {error}
                        </p>
                        <button onClick={handleSearch} className="btn btn-secondary">
                            <RefreshCw className="w-4 h-4" />
                            Try Again
                        </button>
                    </div>
                )}

                {/* Results */}
                {result && !isLoading && (
                    <ResultDisplay result={result} query={query} />
                )}
            </div>
        </div>
    );
};

export default Research;

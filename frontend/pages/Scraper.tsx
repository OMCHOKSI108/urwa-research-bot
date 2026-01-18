import React, { useState } from 'react';
import {
    Globe,
    Loader2,
    Shield,
    AlertTriangle,
    CheckCircle,
    RefreshCw,
    Copy,
    Check,
    ExternalLink,
    Zap,
    Clock,
    Info,
    Download,
    Play
} from 'lucide-react';
import { profileSite, smartScrape, SiteProfile, ScrapeResult, exportToJSON } from '../services/api';
import { useToast } from '../components/Toast';

/* ═══════════════════════════════════════════════════════════════════════════
   PROTECTION LEVEL BADGE
   ═══════════════════════════════════════════════════════════════════════════ */
const ProtectionBadge: React.FC<{ level: string }> = ({ level }) => {
    const config: Record<string, { color: string; bg: string; icon: React.ElementType }> = {
        none: { color: 'var(--success)', bg: 'var(--success-bg)', icon: CheckCircle },
        low: { color: 'var(--success)', bg: 'var(--success-bg)', icon: CheckCircle },
        medium: { color: 'var(--warning)', bg: 'var(--warning-bg)', icon: AlertTriangle },
        high: { color: 'var(--error)', bg: 'var(--error-bg)', icon: Shield },
        extreme: { color: 'var(--error)', bg: 'var(--error-bg)', icon: Shield },
    };

    const c = config[level] || config.medium;
    const Icon = c.icon;

    return (
        <span
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold"
            style={{ background: c.bg, color: c.color }}
        >
            <Icon className="w-4 h-4" />
            {level.charAt(0).toUpperCase() + level.slice(1)} Protection
        </span>
    );
};

/* ═══════════════════════════════════════════════════════════════════════════
   SITE PROFILE DISPLAY
   ═══════════════════════════════════════════════════════════════════════════ */
const SiteProfileDisplay: React.FC<{ profile: SiteProfile }> = ({ profile }) => {
    return (
        <div className="saas-card p-6 animate-slide-up">
            <div className="flex items-start justify-between mb-4">
                <div>
                    <h3 className="font-semibold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                        <Globe className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                        {profile.domain}
                    </h3>
                </div>
                <ProtectionBadge level={profile.protection_level} />
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
                <div
                    className="p-4 rounded-lg"
                    style={{ background: 'var(--bg-muted)' }}
                >
                    <p className="text-xs font-semibold uppercase mb-1" style={{ color: 'var(--text-muted)' }}>
                        Success Rate
                    </p>
                    <p className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
                        {profile.estimated_success_rate}%
                    </p>
                </div>

                <div
                    className="p-4 rounded-lg"
                    style={{ background: 'var(--bg-muted)' }}
                >
                    <p className="text-xs font-semibold uppercase mb-1" style={{ color: 'var(--text-muted)' }}>
                        Strategy
                    </p>
                    <p className="text-lg font-semibold" style={{ color: 'var(--primary)' }}>
                        {profile.recommended_strategy}
                    </p>
                </div>
            </div>

            {/* Bot Detection */}
            {profile.bot_detection.length > 0 && (
                <div className="mt-4">
                    <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
                        Detected Protections:
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {profile.bot_detection.map((detection, idx) => (
                            <span
                                key={idx}
                                className="px-2 py-1 text-xs rounded font-medium"
                                style={{ background: 'var(--warning-bg)', color: 'var(--warning)' }}
                            >
                                {detection}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Warnings */}
            {profile.warnings && profile.warnings.length > 0 && (
                <div
                    className="mt-4 p-3 rounded-lg flex gap-3"
                    style={{ background: 'var(--warning-bg)' }}
                >
                    <AlertTriangle className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--warning)' }} />
                    <div>
                        {profile.warnings.map((warning, idx) => (
                            <p key={idx} className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                {warning}
                            </p>
                        ))}
                    </div>
                </div>
            )}

            {/* Features */}
            <div className="mt-4 flex gap-4">
                <span
                    className={`text-sm flex items-center gap-1 ${profile.requires_js ? '' : 'opacity-50'}`}
                    style={{ color: profile.requires_js ? 'var(--warning)' : 'var(--text-muted)' }}
                >
                    <Zap className="w-4 h-4" />
                    {profile.requires_js ? 'Requires JavaScript' : 'No JS Required'}
                </span>
            </div>
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════════════
   SCRAPE RESULT DISPLAY
   ═══════════════════════════════════════════════════════════════════════════ */
const ScrapeResultDisplay: React.FC<{ result: ScrapeResult; url: string }> = ({ result, url }) => {
    const [copied, setCopied] = useState(false);
    const toast = useToast();

    const handleCopy = async () => {
        if (result.content) {
            await navigator.clipboard.writeText(result.content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
            toast.success('Copied!', 'Content copied to clipboard');
        }
    };

    const handleExport = () => {
        exportToJSON(result, `scrape_${new URL(url).hostname}`);
        toast.success('Exported', 'Data exported to JSON file');
    };

    return (
        <div className="space-y-4 animate-slide-up">
            {/* Status Header */}
            <div className="saas-card p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div
                        className="p-2 rounded-lg"
                        style={{
                            background: result.status === 'success' ? 'var(--success-bg)' : 'var(--error-bg)'
                        }}
                    >
                        {result.status === 'success' ? (
                            <CheckCircle className="w-5 h-5" style={{ color: 'var(--success)' }} />
                        ) : (
                            <AlertTriangle className="w-5 h-5" style={{ color: 'var(--error)' }} />
                        )}
                    </div>
                    <div>
                        <p className="font-medium" style={{ color: 'var(--text-primary)' }}>
                            {result.status === 'success' ? 'Scrape Successful' : 'Scrape Failed'}
                        </p>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            {url}
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {result.execution_time && (
                        <span className="badge badge-info">
                            <Clock className="w-3 h-3" />
                            {result.execution_time.toFixed(2)}s
                        </span>
                    )}
                    {result.strategy_used && (
                        <span className="badge badge-primary">
                            {result.strategy_used}
                        </span>
                    )}
                </div>
            </div>

            {/* Content */}
            {result.content && (
                <div className="saas-card overflow-hidden">
                    <div
                        className="px-4 py-3 flex items-center justify-between"
                        style={{ borderBottom: '1px solid var(--border-light)' }}
                    >
                        <p className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                            Extracted Content ({result.content_length || result.content.length} chars)
                        </p>
                        <div className="flex gap-2">
                            <button onClick={handleCopy} className="btn btn-ghost btn-sm">
                                {copied ? (
                                    <>
                                        <Check className="w-4 h-4" style={{ color: 'var(--success)' }} />
                                        Copied
                                    </>
                                ) : (
                                    <>
                                        <Copy className="w-4 h-4" />
                                        Copy
                                    </>
                                )}
                            </button>
                            <button onClick={handleExport} className="btn btn-secondary btn-sm">
                                <Download className="w-4 h-4" />
                                Export
                            </button>
                        </div>
                    </div>

                    <pre
                        className="p-4 overflow-x-auto text-sm max-h-96"
                        style={{
                            background: 'var(--bg-muted)',
                            color: 'var(--text-secondary)',
                            fontFamily: 'monospace',
                        }}
                    >
                        {result.content.substring(0, 5000)}
                        {result.content.length > 5000 && '\n\n... (truncated)'}
                    </pre>
                </div>
            )}

            {/* Extracted Data */}
            {result.extracted_data && (
                <div className="saas-card p-4">
                    <p className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                        Extracted Data
                    </p>
                    <pre
                        className="p-3 rounded-lg overflow-x-auto text-sm"
                        style={{
                            background: 'var(--bg-muted)',
                            color: 'var(--text-secondary)',
                            fontFamily: 'monospace',
                        }}
                    >
                        {JSON.stringify(result.extracted_data, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN SCRAPER PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
const Scraper: React.FC = () => {
    const toast = useToast();
    const [url, setUrl] = useState('');
    const [instruction, setInstruction] = useState('');
    const [isProfileLoading, setIsProfileLoading] = useState(false);
    const [isScrapeLoading, setIsScrapeLoading] = useState(false);
    const [profile, setProfile] = useState<SiteProfile | null>(null);
    const [scrapeResult, setScrapeResult] = useState<ScrapeResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleProfile = async () => {
        if (!url.trim()) {
            toast.warning('Enter URL', 'Please enter a URL to analyze');
            return;
        }

        setIsProfileLoading(true);
        setError(null);
        setProfile(null);

        try {
            const response = await profileSite(url);
            if (response.success && response.data?.profile) {
                setProfile(response.data.profile);
                toast.success('Analysis Complete', `Recommended strategy: ${response.data.profile.recommended_strategy}`);
            } else {
                throw new Error(response.error || 'Failed to analyze site');
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'An error occurred';
            setError(message);
            toast.error('Analysis Failed', message);
        } finally {
            setIsProfileLoading(false);
        }
    };

    const handleScrape = async () => {
        if (!url.trim()) {
            toast.warning('Enter URL', 'Please enter a URL to scrape');
            return;
        }

        setIsScrapeLoading(true);
        setError(null);
        setScrapeResult(null);

        try {
            const response = await smartScrape(url, instruction || undefined);
            if (response.success && response.data) {
                setScrapeResult(response.data);
                toast.success('Scrape Complete', `Strategy used: ${response.data.strategy_used}`);
            } else {
                throw new Error(response.error || 'Scrape failed');
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'An error occurred';
            setError(message);
            toast.error('Scrape Failed', message);
        } finally {
            setIsScrapeLoading(false);
        }
    };

    const isLoading = isProfileLoading || isScrapeLoading;

    return (
        <div
            className="h-full overflow-y-auto"
            style={{ background: 'var(--bg-base)' }}
        >
            <div className="p-8 max-w-4xl mx-auto space-y-8">

                {/* Header */}
                <header>
                    <h1
                        className="text-2xl font-bold font-display mb-1"
                        style={{ color: 'var(--text-primary)' }}
                    >
                        Web Scraper
                    </h1>
                    <p style={{ color: 'var(--text-muted)' }}>
                        Intelligent extraction with automatic strategy selection
                    </p>
                </header>

                {/* Input Form */}
                <div className="saas-card-elevated p-6 space-y-4">
                    {/* URL Input */}
                    <div>
                        <label
                            className="block text-sm font-medium mb-2"
                            style={{ color: 'var(--text-secondary)' }}
                        >
                            Target URL
                        </label>
                        <div
                            className="flex rounded-xl overflow-hidden"
                            style={{
                                background: 'var(--bg-muted)',
                                border: '1px solid var(--border-light)',
                            }}
                        >
                            <div className="px-4 flex items-center" style={{ color: 'var(--text-muted)' }}>
                                <Globe className="w-5 h-5" />
                            </div>
                            <input
                                type="url"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="https://example.com"
                                className="flex-1 py-3 pr-4 bg-transparent focus:outline-none"
                                style={{ color: 'var(--text-primary)' }}
                            />
                        </div>
                    </div>

                    {/* Instruction Input */}
                    <div>
                        <label
                            className="block text-sm font-medium mb-2 flex items-center gap-1"
                            style={{ color: 'var(--text-secondary)' }}
                        >
                            Extraction Instruction
                            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>(optional)</span>
                        </label>
                        <textarea
                            value={instruction}
                            onChange={(e) => setInstruction(e.target.value)}
                            placeholder="e.g., Extract all article titles and their publish dates"
                            className="input"
                            style={{ minHeight: '80px', resize: 'vertical' }}
                        />
                    </div>

                    {/* Info Box */}
                    <div
                        className="p-3 rounded-lg flex gap-3"
                        style={{ background: 'var(--info-bg)' }}
                    >
                        <Info className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--info)' }} />
                        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                            <strong>Tip:</strong> Use "Analyze Site" first to check protection levels before scraping.
                            The scraper will automatically select the best strategy.
                        </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                        <button
                            onClick={handleProfile}
                            disabled={!url.trim() || isLoading}
                            className="btn btn-secondary flex-1"
                        >
                            {isProfileLoading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Analyzing...
                                </>
                            ) : (
                                <>
                                    <Shield className="w-4 h-4" />
                                    Analyze Site
                                </>
                            )}
                        </button>

                        <button
                            onClick={handleScrape}
                            disabled={!url.trim() || isLoading}
                            className="btn btn-primary flex-1"
                        >
                            {isScrapeLoading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Scraping...
                                </>
                            ) : (
                                <>
                                    <Play className="w-4 h-4" />
                                    Start Scrape
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Error State */}
                {error && !isLoading && (
                    <div
                        className="saas-card p-4 flex items-start gap-3"
                        style={{ borderColor: 'var(--error)' }}
                    >
                        <AlertTriangle className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--error)' }} />
                        <div>
                            <p className="font-medium" style={{ color: 'var(--error)' }}>Error</p>
                            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>{error}</p>
                        </div>
                        <button onClick={() => setError(null)} className="ml-auto btn btn-ghost btn-sm">
                            <RefreshCw className="w-4 h-4" />
                        </button>
                    </div>
                )}

                {/* Site Profile */}
                {profile && !isLoading && (
                    <SiteProfileDisplay profile={profile} />
                )}

                {/* Scrape Result */}
                {scrapeResult && !isLoading && (
                    <ScrapeResultDisplay result={scrapeResult} url={url} />
                )}
            </div>
        </div>
    );
};

export default Scraper;

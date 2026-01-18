import React, { useState, useEffect } from 'react';
import {
    Settings as SettingsIcon,
    Key,
    Check,
    X,
    Loader2,
    AlertCircle,
    Zap,
    Bot,
    Cloud,
    Server,
    Eye,
    EyeOff,
    RefreshCw,
    Save,
    TestTube,
    ChevronDown,
    Info
} from 'lucide-react';
import { useToast } from '../components/Toast';

/* ═══════════════════════════════════════════════════════════════════════════
   LLM PROVIDER TYPES
   ═══════════════════════════════════════════════════════════════════════════ */
type LLMProvider = 'gemini' | 'groq' | 'ollama';

interface ProviderConfig {
    id: LLMProvider;
    name: string;
    description: string;
    icon: React.ElementType;
    color: string;
    bg: string;
    requiresApiKey: boolean;
    supportsModels: boolean;
    defaultModel?: string;
    models?: string[];
}

interface LLMSettings {
    activeProvider: LLMProvider;
    gemini: {
        apiKey: string;
        model: string;
        enabled: boolean;
        status: 'untested' | 'valid' | 'invalid';
    };
    groq: {
        apiKey: string;
        model: string;
        enabled: boolean;
        status: 'untested' | 'valid' | 'invalid';
    };
    ollama: {
        baseUrl: string;
        model: string;
        enabled: boolean;
        status: 'untested' | 'valid' | 'invalid';
    };
}

/* ═══════════════════════════════════════════════════════════════════════════
   PROVIDER CONFIGURATIONS
   ═══════════════════════════════════════════════════════════════════════════ */
const PROVIDERS: ProviderConfig[] = [
    {
        id: 'gemini',
        name: 'Google Gemini',
        description: 'Google\'s most capable AI model. Best for complex reasoning.',
        icon: Zap,
        color: '#4285F4',
        bg: 'rgba(66, 133, 244, 0.1)',
        requiresApiKey: true,
        supportsModels: true,
        defaultModel: 'gemini-2.5-flash',
        models: ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-1.5-pro', 'gemini-1.5-flash'],
    },
    {
        id: 'groq',
        name: 'Groq',
        description: 'Ultra-fast inference. Great for quick responses.',
        icon: Bot,
        color: '#F55036',
        bg: 'rgba(245, 80, 54, 0.1)',
        requiresApiKey: true,
        supportsModels: true,
        defaultModel: 'llama-3.3-70b-versatile',
        models: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
    },
    {
        id: 'ollama',
        name: 'Ollama (Local)',
        description: 'Run models locally. Private and free.',
        icon: Server,
        color: '#00D084',
        bg: 'rgba(0, 208, 132, 0.1)',
        requiresApiKey: false,
        supportsModels: true,
        defaultModel: 'llama3.2',
        models: ['llama3.2', 'llama3.1', 'mistral', 'codellama', 'phi3', 'gemma2'],
    },
];

/* ═══════════════════════════════════════════════════════════════════════════
   STORAGE UTILITIES
   ═══════════════════════════════════════════════════════════════════════════ */
const STORAGE_KEY = 'urwa_llm_settings';

function loadSettings(): LLMSettings {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            return JSON.parse(saved);
        }
    } catch (e) {
        console.error('Failed to load settings:', e);
    }

    return {
        activeProvider: 'gemini',
        gemini: { apiKey: '', model: 'gemini-2.5-flash', enabled: true, status: 'untested' },
        groq: { apiKey: '', model: 'llama-3.3-70b-versatile', enabled: false, status: 'untested' },
        ollama: { baseUrl: 'http://localhost:11434', model: 'llama3.2', enabled: false, status: 'untested' },
    };
}

function saveSettings(settings: LLMSettings): void {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (e) {
        console.error('Failed to save settings:', e);
    }
}

// Export for use in other components
export function getActiveProvider(): { provider: LLMProvider; useOllama: boolean; model: string } {
    const settings = loadSettings();
    return {
        provider: settings.activeProvider,
        useOllama: settings.activeProvider === 'ollama',
        model: settings[settings.activeProvider].model,
    };
}

/* ═══════════════════════════════════════════════════════════════════════════
   API KEY INPUT COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
interface ApiKeyInputProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    disabled?: boolean;
}

const ApiKeyInput: React.FC<ApiKeyInputProps> = ({ value, onChange, placeholder, disabled }) => {
    const [visible, setVisible] = useState(false);

    return (
        <div className="relative">
            <input
                type={visible ? 'text' : 'password'}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder || 'Enter API key...'}
                disabled={disabled}
                className="input pr-10 font-mono text-sm"
                style={{ letterSpacing: visible ? 'normal' : '0.1em' }}
            />
            <button
                type="button"
                onClick={() => setVisible(!visible)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-gray-100"
                style={{ color: 'var(--text-muted)' }}
            >
                {visible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════════════
   PROVIDER CARD COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
interface ProviderCardProps {
    provider: ProviderConfig;
    settings: LLMSettings;
    isActive: boolean;
    onSelect: () => void;
    onUpdateSettings: (key: string, value: any) => void;
    onTest: () => void;
    isTesting: boolean;
}

const ProviderCard: React.FC<ProviderCardProps> = ({
    provider,
    settings,
    isActive,
    onSelect,
    onUpdateSettings,
    onTest,
    isTesting,
}) => {
    const providerSettings = settings[provider.id];
    const Icon = provider.icon;

    const statusConfig = {
        untested: { label: 'Not Tested', color: 'var(--text-muted)', icon: AlertCircle },
        valid: { label: 'Connected', color: 'var(--success)', icon: Check },
        invalid: { label: 'Invalid', color: 'var(--error)', icon: X },
    };

    const status = statusConfig[providerSettings.status];
    const StatusIcon = status.icon;

    return (
        <div
            className={`saas-card p-5 transition-all`}
            style={{
                borderColor: isActive ? provider.color : 'var(--border-light)',
                outline: isActive ? `2px solid ${provider.color}` : 'none',
                outlineOffset: '2px',
            }}
        >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div
                        className="p-2.5 rounded-xl"
                        style={{ background: provider.bg }}
                    >
                        <Icon className="w-5 h-5" style={{ color: provider.color }} />
                    </div>
                    <div>
                        <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                            {provider.name}
                        </h3>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            {provider.description}
                        </p>
                    </div>
                </div>

                {/* Active Toggle */}
                <button
                    onClick={onSelect}
                    className={`relative w-12 h-6 rounded-full transition-all ${isActive ? '' : 'opacity-60'}`}
                    style={{
                        background: isActive ? provider.color : 'var(--bg-muted)',
                    }}
                >
                    <div
                        className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow-sm transition-all ${isActive ? 'left-7' : 'left-1'
                            }`}
                    />
                </button>
            </div>

            {/* Status */}
            <div
                className="flex items-center gap-2 mb-4 px-3 py-2 rounded-lg"
                style={{ background: 'var(--bg-muted)' }}
            >
                <StatusIcon className="w-4 h-4" style={{ color: status.color }} />
                <span className="text-sm font-medium" style={{ color: status.color }}>
                    {status.label}
                </span>
            </div>

            {/* Configuration */}
            <div className="space-y-4">
                {/* API Key (for cloud providers) */}
                {provider.requiresApiKey && (
                    <div>
                        <label
                            className="block text-sm font-medium mb-1.5"
                            style={{ color: 'var(--text-secondary)' }}
                        >
                            API Key
                        </label>
                        <ApiKeyInput
                            value={(providerSettings as any).apiKey || ''}
                            onChange={(value) => onUpdateSettings('apiKey', value)}
                            placeholder={`Enter ${provider.name} API key...`}
                        />
                    </div>
                )}

                {/* Base URL (for Ollama) */}
                {provider.id === 'ollama' && (
                    <div>
                        <label
                            className="block text-sm font-medium mb-1.5"
                            style={{ color: 'var(--text-secondary)' }}
                        >
                            Ollama URL
                        </label>
                        <input
                            type="text"
                            value={(providerSettings as any).baseUrl || 'http://localhost:11434'}
                            onChange={(e) => onUpdateSettings('baseUrl', e.target.value)}
                            placeholder="http://localhost:11434"
                            className="input font-mono text-sm"
                        />
                    </div>
                )}

                {/* Model Selection */}
                {provider.supportsModels && provider.models && (
                    <div>
                        <label
                            className="block text-sm font-medium mb-1.5"
                            style={{ color: 'var(--text-secondary)' }}
                        >
                            Model
                        </label>
                        <div className="relative">
                            <select
                                value={providerSettings.model}
                                onChange={(e) => onUpdateSettings('model', e.target.value)}
                                className="input appearance-none cursor-pointer pr-10"
                            >
                                {provider.models.map((model) => (
                                    <option key={model} value={model}>
                                        {model}
                                    </option>
                                ))}
                            </select>
                            <ChevronDown
                                className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                                style={{ color: 'var(--text-muted)' }}
                            />
                        </div>
                    </div>
                )}

                {/* Test Button */}
                <button
                    onClick={onTest}
                    disabled={isTesting || (provider.requiresApiKey && !(providerSettings as any).apiKey)}
                    className="btn btn-secondary w-full"
                >
                    {isTesting ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Testing Connection...
                        </>
                    ) : (
                        <>
                            <TestTube className="w-4 h-4" />
                            Test Connection
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN SETTINGS PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
const Settings: React.FC = () => {
    const toast = useToast();
    const [settings, setSettings] = useState<LLMSettings>(loadSettings);
    const [testingProvider, setTestingProvider] = useState<LLMProvider | null>(null);
    const [hasChanges, setHasChanges] = useState(false);

    // Save to localStorage when settings change
    useEffect(() => {
        if (hasChanges) {
            saveSettings(settings);
        }
    }, [settings, hasChanges]);

    const handleSelectProvider = (providerId: LLMProvider) => {
        // If clicking the already active provider, show a warning (can't turn off - one must be active)
        if (settings.activeProvider === providerId) {
            toast.warning('Cannot Disable', 'At least one LLM provider must be active. Select another provider to switch.');
            return;
        }

        setSettings(prev => ({
            ...prev,
            activeProvider: providerId,
            gemini: { ...prev.gemini, enabled: providerId === 'gemini' },
            groq: { ...prev.groq, enabled: providerId === 'groq' },
            ollama: { ...prev.ollama, enabled: providerId === 'ollama' },
        }));
        setHasChanges(true);
        toast.success('Provider Changed', `Now using ${PROVIDERS.find(p => p.id === providerId)?.name}`);
    };

    const handleUpdateProviderSettings = (providerId: LLMProvider, key: string, value: any) => {
        setSettings(prev => ({
            ...prev,
            [providerId]: {
                ...prev[providerId],
                [key]: value,
                status: 'untested', // Reset status when config changes
            },
        }));
        setHasChanges(true);
    };

    const handleTestProvider = async (providerId: LLMProvider) => {
        setTestingProvider(providerId);

        try {
            const providerSettings = settings[providerId];
            let testEndpoint = '';
            let testBody = {};

            if (providerId === 'gemini') {
                // Test Gemini API
                const geminiSettings = settings.gemini;
                testEndpoint = `https://generativelanguage.googleapis.com/v1beta/models/${geminiSettings.model}:generateContent?key=${geminiSettings.apiKey}`;
                testBody = {
                    contents: [{ parts: [{ text: 'Say "API connection successful" in exactly 4 words.' }] }],
                };

                const response = await fetch(testEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(testBody),
                });

                if (response.ok) {
                    setSettings(prev => ({
                        ...prev,
                        [providerId]: { ...prev[providerId], status: 'valid' },
                    }));
                    toast.success('Connection Successful', `${PROVIDERS.find(p => p.id === providerId)?.name} API is working!`);
                } else {
                    throw new Error('Invalid API key or model');
                }
            } else if (providerId === 'groq') {
                // Test Groq API
                const groqSettings = settings.groq;
                testEndpoint = 'https://api.groq.com/openai/v1/chat/completions';
                testBody = {
                    model: groqSettings.model,
                    messages: [{ role: 'user', content: 'Say "OK"' }],
                    max_tokens: 10,
                };

                const response = await fetch(testEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${groqSettings.apiKey}`,
                    },
                    body: JSON.stringify(testBody),
                });

                if (response.ok) {
                    setSettings(prev => ({
                        ...prev,
                        [providerId]: { ...prev[providerId], status: 'valid' },
                    }));
                    toast.success('Connection Successful', 'Groq API is working!');
                } else {
                    throw new Error('Invalid API key or model');
                }
            } else if (providerId === 'ollama') {
                // Test Ollama local server
                const ollamaSettings = settings.ollama;
                const baseUrl = ollamaSettings.baseUrl || 'http://localhost:11434';
                const response = await fetch(`${baseUrl}/api/tags`, {
                    method: 'GET',
                    signal: AbortSignal.timeout(5000),
                });

                if (response.ok) {
                    const data = await response.json();
                    const models = data.models?.map((m: any) => m.name) || [];

                    if (models.length > 0) {
                        setSettings(prev => ({
                            ...prev,
                            [providerId]: { ...prev[providerId], status: 'valid' },
                        }));
                        toast.success('Ollama Connected', `Found ${models.length} models available`);
                    } else {
                        throw new Error('No models found. Pull a model first with: ollama pull llama3.2');
                    }
                } else {
                    throw new Error('Could not connect to Ollama');
                }
            }
        } catch (error) {
            setSettings(prev => ({
                ...prev,
                [providerId]: { ...prev[providerId], status: 'invalid' },
            }));
            toast.error('Connection Failed', error instanceof Error ? error.message : 'Unknown error');
        } finally {
            setTestingProvider(null);
            setHasChanges(true);
        }
    };

    return (
        <div
            className="h-full overflow-y-auto"
            style={{ background: 'var(--bg-base)' }}
        >
            <div className="p-8 max-w-4xl mx-auto space-y-8">

                {/* Header */}
                <header>
                    <div className="flex items-center gap-3 mb-2">
                        <div
                            className="p-2 rounded-lg"
                            style={{ background: 'var(--primary-bg)' }}
                        >
                            <SettingsIcon className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                        </div>
                        <h1
                            className="text-2xl font-bold font-display"
                            style={{ color: 'var(--text-primary)' }}
                        >
                            Settings
                        </h1>
                    </div>
                    <p style={{ color: 'var(--text-muted)' }}>
                        Configure your AI providers and preferences
                    </p>
                </header>

                {/* Info Box */}
                <div
                    className="p-4 rounded-xl flex gap-3"
                    style={{ background: 'var(--info-bg)', border: '1px solid rgba(37, 99, 235, 0.2)' }}
                >
                    <Info className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--info)' }} />
                    <div>
                        <p className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                            Choose Your AI Provider
                        </p>
                        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
                            Select one provider to use for all AI operations. Toggle the switch to activate it.
                            Use the Test button to verify your API key or connection before using.
                        </p>
                    </div>
                </div>

                {/* Active Provider Indicator */}
                <div
                    className="saas-card p-4 flex items-center justify-between"
                    style={{ borderColor: PROVIDERS.find(p => p.id === settings.activeProvider)?.color }}
                >
                    <div className="flex items-center gap-3">
                        <Cloud className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                        <span className="font-medium" style={{ color: 'var(--text-primary)' }}>
                            Active Provider:
                        </span>
                        <span
                            className="px-3 py-1 rounded-full text-sm font-semibold"
                            style={{
                                background: PROVIDERS.find(p => p.id === settings.activeProvider)?.bg,
                                color: PROVIDERS.find(p => p.id === settings.activeProvider)?.color,
                            }}
                        >
                            {PROVIDERS.find(p => p.id === settings.activeProvider)?.name}
                        </span>
                    </div>

                    {hasChanges && (
                        <span
                            className="text-xs flex items-center gap-1"
                            style={{ color: 'var(--success)' }}
                        >
                            <Check className="w-3 h-3" />
                            Settings saved automatically
                        </span>
                    )}
                </div>

                {/* Provider Cards */}
                <section className="grid grid-cols-1 gap-6">
                    {PROVIDERS.map((provider) => (
                        <ProviderCard
                            key={provider.id}
                            provider={provider}
                            settings={settings}
                            isActive={settings.activeProvider === provider.id}
                            onSelect={() => handleSelectProvider(provider.id)}
                            onUpdateSettings={(key, value) => handleUpdateProviderSettings(provider.id, key, value)}
                            onTest={() => handleTestProvider(provider.id)}
                            isTesting={testingProvider === provider.id}
                        />
                    ))}
                </section>

                {/* Advanced Settings */}
                <section className="saas-card p-6">
                    <h3
                        className="font-semibold mb-4"
                        style={{ color: 'var(--text-primary)' }}
                    >
                        System Information
                    </h3>

                    <div className="grid grid-cols-2 gap-4">
                        <div
                            className="p-4 rounded-lg"
                            style={{ background: 'var(--bg-muted)' }}
                        >
                            <p className="text-xs uppercase font-semibold" style={{ color: 'var(--text-muted)' }}>
                                Frontend Version
                            </p>
                            <p className="text-lg font-mono font-semibold mt-1" style={{ color: 'var(--text-primary)' }}>
                                v3.5.0
                            </p>
                        </div>

                        <div
                            className="p-4 rounded-lg"
                            style={{ background: 'var(--bg-muted)' }}
                        >
                            <p className="text-xs uppercase font-semibold" style={{ color: 'var(--text-muted)' }}>
                                Backend API
                            </p>
                            <p className="text-lg font-mono font-semibold mt-1" style={{ color: 'var(--text-primary)' }}>
                                {import.meta.env.VITE_API_BASE ? 'Connected' : 'Local / Dev'}
                            </p>
                        </div>
                    </div>

                    <div className="mt-4 flex gap-3">
                        <button
                            onClick={() => {
                                localStorage.removeItem(STORAGE_KEY);
                                setSettings(loadSettings());
                                toast.success('Settings Reset', 'All settings have been reset to defaults');
                            }}
                            className="btn btn-ghost"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Reset to Defaults
                        </button>
                    </div>
                </section>
            </div>
        </div>
    );
};

export default Settings;

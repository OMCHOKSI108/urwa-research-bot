import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { Toast } from '../types';

interface ToastContextType {
    toasts: Toast[];
    addToast: (toast: Omit<Toast, 'id'>) => void;
    removeToast: (id: string) => void;
    success: (title: string, message?: string) => void;
    error: (title: string, message?: string) => void;
    warning: (title: string, message?: string) => void;
    info: (title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
}

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
        const id = Math.random().toString(36).substring(2, 9);
        const newToast = { ...toast, id };
        setToasts((prev) => [...prev, newToast]);

        // Auto-remove after duration
        const duration = toast.duration ?? 5000;
        setTimeout(() => {
            removeToast(id);
        }, duration);
    }, []);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const success = useCallback((title: string, message?: string) => {
        addToast({ type: 'success', title, message });
    }, [addToast]);

    const error = useCallback((title: string, message?: string) => {
        addToast({ type: 'error', title, message, duration: 8000 });
    }, [addToast]);

    const warning = useCallback((title: string, message?: string) => {
        addToast({ type: 'warning', title, message });
    }, [addToast]);

    const info = useCallback((title: string, message?: string) => {
        addToast({ type: 'info', title, message });
    }, [addToast]);

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
            {children}
            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </ToastContext.Provider>
    );
}

// Toast Container Component
function ToastContainer({
    toasts,
    onRemove
}: {
    toasts: Toast[];
    onRemove: (id: string) => void;
}) {
    if (toasts.length === 0) return null;

    return (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-md">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
            ))}
        </div>
    );
}

// Individual Toast Component
function ToastItem({
    toast,
    onRemove
}: {
    toast: Toast;
    onRemove: (id: string) => void;
}) {
    const icons = {
        success: <CheckCircle className="w-5 h-5" style={{ color: 'var(--success)' }} />,
        error: <AlertCircle className="w-5 h-5" style={{ color: 'var(--error)' }} />,
        warning: <AlertTriangle className="w-5 h-5" style={{ color: 'var(--warning)' }} />,
        info: <Info className="w-5 h-5" style={{ color: 'var(--info)' }} />,
    };

    const backgrounds = {
        success: 'var(--success-bg)',
        error: 'var(--error-bg)',
        warning: 'var(--warning-bg)',
        info: 'var(--info-bg)',
    };

    return (
        <div
            className="animate-slide-up"
            style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-xl)',
                overflow: 'hidden',
            }}
        >
            {/* Progress bar */}
            <div
                className="h-1"
                style={{
                    background: backgrounds[toast.type],
                }}
            >
                <div
                    className="h-full"
                    style={{
                        background: toast.type === 'success' ? 'var(--success)'
                            : toast.type === 'error' ? 'var(--error)'
                                : toast.type === 'warning' ? 'var(--warning)'
                                    : 'var(--info)',
                        animation: `shrink ${toast.duration || 5000}ms linear forwards`,
                    }}
                />
            </div>

            <div className="flex items-start gap-3 p-4">
                <div className="flex-shrink-0 mt-0.5">
                    {icons[toast.type]}
                </div>

                <div className="flex-1 min-w-0">
                    <p
                        className="font-semibold text-sm"
                        style={{ color: 'var(--text-primary)' }}
                    >
                        {toast.title}
                    </p>
                    {toast.message && (
                        <p
                            className="text-sm mt-1"
                            style={{ color: 'var(--text-secondary)' }}
                        >
                            {toast.message}
                        </p>
                    )}
                </div>

                <button
                    onClick={() => onRemove(toast.id)}
                    className="flex-shrink-0 p-1 rounded-md transition-colors hover:bg-gray-100"
                    style={{ color: 'var(--text-muted)' }}
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            <style>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
        </div>
    );
}

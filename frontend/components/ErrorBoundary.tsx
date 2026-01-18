import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  private handleGoHome = () => {
    window.location.hash = '/';
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          className="h-full flex items-center justify-center p-8"
          style={{ background: 'var(--bg-base)' }}
        >
          <div className="text-center max-w-md">
            {/* Error Icon */}
            <div
              className="w-16 h-16 mx-auto mb-6 rounded-2xl flex items-center justify-center"
              style={{ background: 'var(--error-bg)' }}
            >
              <AlertTriangle
                className="w-8 h-8"
                style={{ color: 'var(--error)' }}
              />
            </div>

            {/* Error Title */}
            <h2
              className="text-xl font-bold mb-2"
              style={{ color: 'var(--text-primary)' }}
            >
              Something went wrong
            </h2>

            {/* Error Description */}
            <p
              className="text-sm mb-6"
              style={{ color: 'var(--text-muted)' }}
            >
              An unexpected error occurred while rendering this page.
              Please try again or return to the dashboard.
            </p>

            {/* Error Details (collapsible) */}
            {this.state.error && (
              <details
                className="mb-6 text-left p-4 rounded-lg"
                style={{
                  background: 'var(--bg-muted)',
                  border: '1px solid var(--border-light)',
                }}
              >
                <summary
                  className="cursor-pointer text-sm font-medium"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  Error Details
                </summary>
                <pre
                  className="mt-2 text-xs overflow-x-auto font-mono"
                  style={{ color: 'var(--error)' }}
                >
                  {this.state.error.toString()}
                </pre>
                {this.state.errorInfo && (
                  <pre
                    className="mt-2 text-xs overflow-x-auto font-mono max-h-40"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </details>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleRetry}
                className="btn btn-primary"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>
              <button
                onClick={this.handleGoHome}
                className="btn btn-secondary"
              >
                <Home className="w-4 h-4" />
                Go to Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
/**
 * Global Error Boundary — Catches unhandled React render errors gracefully.
 * Provides a user-friendly recovery UI instead of a blank screen.
 */
import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // In production, send to an error tracking service (e.g. Sentry)
    console.error('[ErrorBoundary] Unhandled React error:', error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen w-screen flex-col items-center justify-center bg-background p-6 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-destructive/10 text-destructive mb-4 border border-destructive/20">
            <AlertTriangle size={32} />
          </div>
          <h1 className="text-xl font-bold text-foreground mb-2">Something went wrong</h1>
          <p className="text-[13px] text-muted-foreground max-w-md mb-2 leading-relaxed">
            An unexpected error occurred in VisionArchive. The error has been logged. Please reload to continue.
          </p>
          {this.state.error?.message && (
            <code className="text-[11px] mono text-muted-foreground/70 bg-muted px-3 py-1.5 rounded-md mb-6 max-w-sm truncate block">
              {this.state.error.message}
            </code>
          )}
          <button
            onClick={this.handleReload}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground hover:bg-primary/90 transition-colors shadow-md"
          >
            <RefreshCw size={14} />
            Reload VisionArchive
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useAnalysis } from '../../context/AnalysisContext';
import { AlertCircle, RefreshCw } from 'lucide-react';

export function Layout({ children }) {
  const { error, backendHealth, checkHealthStatus } = useAnalysis();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />

        {/* Global Alert Notification for Backend Disconnection or Error */}
        {backendHealth === 'offline' && (
          <div className="bg-rose-500/15 border-b border-rose-500/30 px-6 py-2.5 flex items-center justify-between text-xs text-rose-300">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span>
                Backend server is unreachable at <strong className="font-mono">http://127.0.0.1:8001</strong>. Make sure <strong className="font-mono">uvicorn backend.main:app --port 8001</strong> is running.
              </span>
            </div>
            <button
              onClick={checkHealthStatus}
              className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-[11px] font-semibold transition-colors"
            >
              <RefreshCw className="w-3 h-3" /> Reconnect
            </button>
          </div>
        )}

        {error && backendHealth !== 'offline' && (
          <div className="bg-amber-500/15 border-b border-amber-500/30 px-6 py-2.5 flex items-center gap-2 text-xs text-amber-300">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">
          <div className="max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

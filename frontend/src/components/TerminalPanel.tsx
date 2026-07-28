import { useEffect, useRef, useState } from "react";
import { useIDEStore } from "../store/ideStore";

export function TerminalPanel() {
  const { terminalLogs, clearLogs } = useIDEStore();
  const terminalRef = useRef<HTMLDivElement>(null);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalLogs]);

  if (collapsed) {
    return (
      <div
        className="h-8 bg-editor-sidebar border-t border-editor-border flex items-center px-3 cursor-pointer"
        onClick={() => setCollapsed(false)}
      >
        <span className="text-xs text-gray-500">Terminal ({terminalLogs.length} righe)</span>
      </div>
    );
  }

  return (
    <div className="h-48 border-t border-editor-border flex flex-col bg-editor-bg">
      <div className="flex items-center justify-between px-3 py-1 bg-editor-sidebar border-b border-editor-border">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-editor-text uppercase tracking-wider">
            Terminal
          </span>
          {terminalLogs.length > 0 && (
            <span className="text-[10px] bg-editor-accent text-white rounded px-1.5 py-0.5">
              {terminalLogs.length}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={clearLogs}
            className="text-[10px] text-gray-500 hover:text-editor-text px-1.5 py-0.5 rounded hover:bg-editor-border"
          >
            Clear
          </button>
          <button
            onClick={() => setCollapsed(true)}
            className="text-gray-500 hover:text-editor-text px-1 py-0.5 rounded hover:bg-editor-border"
          >
            ▾
          </button>
        </div>
      </div>
      <div
        ref={terminalRef}
        className="flex-1 overflow-y-auto font-mono text-xs p-2 space-y-0.5"
      >
        {terminalLogs.length === 0 ? (
          <span className="text-gray-600 italic">In attesa di output...</span>
        ) : (
          terminalLogs.map((log, i) => (
            <div
              key={i}
              className={`whitespace-pre-wrap ${
                log.startsWith("[ERROR]")
                  ? "text-red-400"
                  : log.startsWith("[OK]") || log.startsWith("[BASIC]") || log.startsWith("[PRG]")
                  ? "text-green-400"
                  : log.startsWith("[C64]")
                  ? "text-yellow-400"
                  : "text-gray-400"
              }`}
            >
              {log}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

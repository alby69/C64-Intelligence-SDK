import { useEffect, useRef, useState } from "react";
import { useIDEStore } from "../store/ideStore";

export function TerminalPanel() {
  const { terminalLogs, clearLogs, commandHistory, addCommandHistory } = useIDEStore();
  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [input, setInput] = useState("");
  const [histIdx, setHistIdx] = useState(-1);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalLogs]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cmd = input.trim();
    if (!cmd) return;

    addCommandHistory(cmd);
    useIDEStore.getState().addLog(`$ ${cmd}`);
    setInput("");
    setHistIdx(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (commandHistory.length === 0) return;
      const newIdx = histIdx < commandHistory.length - 1 ? histIdx + 1 : histIdx;
      setHistIdx(newIdx);
      setInput(commandHistory[commandHistory.length - 1 - newIdx] || "");
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (histIdx <= 0) {
        setHistIdx(-1);
        setInput("");
        return;
      }
      const newIdx = histIdx - 1;
      setHistIdx(newIdx);
      setInput(commandHistory[commandHistory.length - 1 - newIdx] || "");
    }
  };

  if (collapsed) {
    return (
      <div
        className="h-8 bg-editor-sidebar border-t border-editor-border flex items-center justify-between px-3 cursor-pointer hover:bg-editor-border/30 transition-colors"
        onClick={() => setCollapsed(false)}
      >
        <span className="text-xs text-gray-500">
          ▴ Terminal ({terminalLogs.length} righe)
        </span>
      </div>
    );
  }

  return (
    <div className="h-52 border-t border-editor-border flex flex-col bg-editor-bg">
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
            className="text-gray-500 hover:text-editor-text px-1 py-0.5 rounded hover:bg-editor-border text-xs"
            title="Comprimi"
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
          <div className="flex flex-col items-center justify-center h-full">
            <span className="text-gray-600 italic">In attesa di output...</span>
            <span className="text-[10px] text-gray-700 mt-1">
              Compila con Ctrl+B · Esegui con F5 · Digita un comando qui sotto
            </span>
          </div>
        ) : (
          terminalLogs.map((log, i) => {
            const isCmd = log.startsWith("$ ");
            return (
              <div
                key={i}
                className={`whitespace-pre-wrap ${
                  isCmd
                    ? "text-editor-accent font-semibold"
                    : log.startsWith("[ERROR]")
                    ? "text-red-400"
                    : log.startsWith("[OK]")
                    ? "text-green-400"
                    : log.startsWith("[BASIC]") || log.startsWith("[PRG]")
                    ? "text-green-300"
                    : log.startsWith("[C64]")
                    ? "text-yellow-400"
                    : log.startsWith("[BUILD]")
                    ? "text-blue-400"
                    : log.startsWith("[EMU]")
                    ? "text-purple-400"
                    : log.startsWith("[DISK]")
                    ? "text-cyan-400"
                    : log.startsWith("[EDITOR]")
                    ? "text-orange-400"
                    : log.startsWith("[PROJECT]")
                    ? "text-pink-400"
                    : log.startsWith("[PLUGIN]")
                    ? "text-teal-400"
                    : "text-gray-400"
                }`}
              >
                {log}
              </div>
            );
          })
        )}
      </div>
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 px-3 py-1.5 border-t border-editor-border bg-editor-sidebar"
      >
        <span className="text-editor-accent font-mono text-xs">$</span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Digita un comando..."
          className="flex-1 bg-transparent text-xs font-mono text-editor-text outline-none placeholder-gray-600"
        />
      </form>
    </div>
  );
}

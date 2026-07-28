import { useState, useRef, useEffect } from "react";
import { AICopilotClient } from "../services/aiCopilotClient";
import { useIDEStore } from "../store/ideStore";

export function AiCopilotPanel() {
  const { activeFile, fileContents, addLog } = useIDEStore();
  const [prompt, setPrompt] = useState("");
  const [suggestion, setSuggestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [collapsed, setCollapsed] = useState(true);
  const [history, setHistory] = useState<{ prompt: string; result: string }[]>([]);
  const clientRef = useRef<AICopilotClient | null>(null);

  useEffect(() => {
    return () => {
      clientRef.current?.disconnect();
    };
  }, []);

  const handleComplete = () => {
    const p = prompt.trim();
    if (!p || loading) return;

    setLoading(true);
    setSuggestion("");

    const context = activeFile ? (fileContents[activeFile] || "").slice(-500) : "";

    clientRef.current = new AICopilotClient({
      onToken: (token) => {
        setSuggestion((prev) => prev + token);
      },
      onDone: () => {
        setLoading(false);
        setHistory((prev) => [...prev.slice(-10), { prompt: p, result: suggestion + "\n" }]);
      },
      onError: (err) => {
        addLog(`[AI] Errore: ${err}`);
        setLoading(false);
      },
    });

    clientRef.current.complete(p, context);
  };

  const insertSuggestion = () => {
    if (!suggestion || !activeFile) return;
    const current = fileContents[activeFile] || "";
    useIDEStore.getState().updateFileContent(activeFile, current + "\n" + suggestion);
    addLog("[AI] Suggerimento inserito nell'editor");
    setSuggestion("");
  };

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className="fixed bottom-16 right-4 z-50 bg-editor-accent text-white px-3 py-1.5 rounded-full text-xs font-medium shadow-lg hover:bg-editor-accent/80 transition-colors"
        title="AI Copilot"
      >
        🤖 AI
      </button>
    );
  }

  return (
    <div className="fixed bottom-16 right-4 z-50 w-96 bg-editor-sidebar border border-editor-border rounded-lg shadow-2xl overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-editor-border bg-editor-bg">
        <span className="text-xs font-semibold text-editor-text uppercase tracking-wider">
          🤖 AI Copilot
        </span>
        <button
          onClick={() => setCollapsed(true)}
          className="text-gray-500 hover:text-editor-text text-xs px-1"
        >
          ✕
        </button>
      </div>

      <div className="p-3 space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleComplete()}
            placeholder="Chiedi al C64 AI (es. 'ciclo FOR con PRINT')..."
            className="flex-1 bg-editor-bg border border-editor-border rounded px-2 py-1.5 text-xs text-editor-text outline-none focus:border-editor-accent placeholder-gray-600"
          />
          <button
            onClick={handleComplete}
            disabled={loading || !prompt.trim()}
            className="px-3 py-1.5 bg-editor-accent text-white text-xs rounded hover:bg-editor-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "⏳" : "→"}
          </button>
        </div>

        {suggestion && (
          <div className="bg-editor-bg border border-editor-border rounded p-2">
            <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap overflow-x-auto max-h-40 overflow-y-auto">
              {suggestion}
            </pre>
            <div className="flex gap-2 mt-2">
              <button
                onClick={insertSuggestion}
                className="px-2 py-1 bg-green-600/20 text-green-400 text-[10px] rounded hover:bg-green-600/30 transition-colors"
              >
                Inserisci
              </button>
              <button
                onClick={() => setSuggestion("")}
                className="px-2 py-1 bg-editor-border text-gray-400 text-[10px] rounded hover:bg-editor-border/50 transition-colors"
              >
                Ignora
              </button>
            </div>
          </div>
        )}

        {history.length > 0 && (
          <div className="space-y-1">
            <span className="text-[10px] text-gray-600 uppercase">Cronologia</span>
            {history.slice(-3).reverse().map((h, i) => (
              <div
                key={i}
                className="text-[10px] text-gray-500 truncate cursor-pointer hover:text-gray-400"
                onClick={() => {
                  setPrompt(h.prompt);
                  setSuggestion(h.result);
                }}
              >
                <span className="text-editor-accent">Q:</span> {h.prompt}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

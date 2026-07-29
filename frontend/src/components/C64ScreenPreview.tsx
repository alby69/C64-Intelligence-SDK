import { useEffect, useRef, useState } from "react";

export function C64ScreenPreview() {
  const [collapsed, setCollapsed] = useState(true);
  const [output, setOutput] = useState<string[]>([]);
  const [borderColor, setBorderColor] = useState("#0000aa");
  const [bgColor] = useState("#0000aa");
  const [textColor] = useState("#ffffff");
  const screenRef = useRef<HTMLDivElement>(null);
  const [cursorVisible, setCursorVisible] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => setCursorVisible((v) => !v), 500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (screenRef.current) {
      screenRef.current.scrollTop = screenRef.current.scrollHeight;
    }
  }, [output]);

  const addOutput = (text: string) => {
    setOutput((prev) => {
      const lines = [...prev, ...text.split("\n")];
      return lines.slice(-25);
    });
  };

  useEffect(() => {
    const handler = (e: CustomEvent) => addOutput(e.detail);
    window.addEventListener("c64:output" as any, handler);
    return () => window.removeEventListener("c64:output" as any, handler);
  }, []);

  const clearScreen = () => setOutput([]);

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className="fixed bottom-16 right-24 z-50 bg-editor-sidebar border border-editor-border text-editor-text px-3 py-1.5 rounded-full text-xs font-medium shadow-lg hover:border-editor-accent transition-colors"
        title="C64 Screen"
      >
        📺 Screen
      </button>
    );
  }

  return (
    <div className="fixed bottom-16 right-24 z-50 w-[400px] bg-editor-sidebar border border-editor-border rounded-lg shadow-2xl overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-editor-border bg-editor-bg">
        <span className="text-xs font-semibold text-editor-text uppercase tracking-wider">
          📺 C64 Screen
        </span>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <span className="text-[10px] text-gray-500">Bdr</span>
            <input
              type="color"
              value={borderColor}
              onChange={(e) => setBorderColor(e.target.value)}
              className="w-4 h-4 cursor-pointer"
            />
          </div>
          <button
            onClick={clearScreen}
            className="text-[10px] text-gray-500 hover:text-editor-text px-1"
            title="Pulisci"
          >
            CLR
          </button>
          <button
            onClick={() => setCollapsed(true)}
            className="text-gray-500 hover:text-editor-text text-xs px-1"
          >
            ✕
          </button>
        </div>
      </div>

      <div
        className="p-2"
        style={{ backgroundColor: borderColor }}
      >
        <div
          ref={screenRef}
          className="w-full h-64 overflow-y-auto font-mono text-sm leading-tight p-2 rounded"
          style={{
            backgroundColor: bgColor,
            color: textColor,
            fontFamily: "'Courier New', monospace",
          }}
        >
          {output.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <span className="opacity-50 text-xs">
                READY.<br/>
                <span className={cursorVisible ? "opacity-100" : "opacity-0"}>_</span>
              </span>
            </div>
          ) : (
            output.map((line, i) => (
              <div key={i} className="whitespace-pre">
                {line || "\u00A0"}
              </div>
            ))
          )}
          {output.length > 0 && (
            <div className={`mt-0.5 ${cursorVisible ? "opacity-100" : "opacity-0"}`}>
              <span className="text-xs">█</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

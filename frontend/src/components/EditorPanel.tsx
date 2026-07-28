import { useEffect, useRef, useCallback } from "react";
import Editor, { OnMount } from "@monaco-editor/react";
import { useIDEStore } from "../store/ideStore";
import { registerC64Languages } from "../services/monacoLanguages";
import { LSPClient } from "../services/lspClient";

export function EditorPanel() {
  const { activeFile, fileContents, updateFileContent } = useIDEStore();
  const lspRef = useRef<LSPClient | null>(null);
  const editorRef = useRef<any>(null);

  const cleanupLsp = useCallback(() => {
    if (lspRef.current) {
      lspRef.current.disconnect();
      lspRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => cleanupLsp();
  }, [cleanupLsp]);

  useEffect(() => {
    cleanupLsp();
  }, [activeFile, cleanupLsp]);

  const handleEditorMount: OnMount = useCallback(
    (editor, monaco) => {
      editorRef.current = editor;
      registerC64Languages(monaco);

      if (activeFile && activeFile.endsWith(".c64")) {
        const uri = `file:///${activeFile}`;
        lspRef.current = new LSPClient(editor, uri, (diagnostics) => {
          const model = editor.getModel();
          if (!model) return;
          const markers = diagnostics.map((d: any) => ({
            startLineNumber: (d.range?.start?.line ?? 0) + 1,
            startColumn: (d.range?.start?.character ?? 0) + 1,
            endLineNumber: (d.range?.end?.line ?? d.range?.start?.line ?? 0) + 1,
            endColumn: (d.range?.end?.character ?? d.range?.start?.character ?? 0) + 1,
            message: d.message || "Errore",
            severity: monaco.MarkerSeverity.Error,
          }));
          monaco.editor.setModelMarkers(model, "c64-lsp", markers);
        });
      }
    },
    [activeFile]
  );

  const handleChange = useCallback(
    (value: string | undefined) => {
      if (!activeFile) return;
      updateFileContent(activeFile, value || "");
      if (lspRef.current) {
        lspRef.current.notifyChange(value || "");
      }
    },
    [activeFile, updateFileContent]
  );

  if (!activeFile) {
    return (
      <div className="flex-1 flex items-center justify-center bg-editor-bg">
        <div className="text-center">
          <div className="text-6xl mb-4 opacity-30">🖥️</div>
          <h2 className="text-lg font-semibold text-gray-400 mb-2">
            C64 Intelligence Studio
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Apri un file o seleziona un plugin dalla barra laterale
          </p>
          <div className="flex flex-col items-center gap-2 text-[11px] text-gray-600">
            <span>
              <kbd className="px-1.5 py-0.5 bg-editor-sidebar border border-editor-border rounded text-gray-500">
                Ctrl+O
              </kbd>{" "}
              Apri file
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 bg-editor-sidebar border border-editor-border rounded text-gray-500">
                Ctrl+S
              </kbd>{" "}
              Salva
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 bg-editor-sidebar border border-editor-border rounded text-gray-500">
                Ctrl+B
              </kbd>{" "}
              Compila
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 bg-editor-sidebar border border-editor-border rounded text-gray-500">
                F5
              </kbd>{" "}
              Esegui
            </span>
          </div>
        </div>
      </div>
    );
  }

  const ext = activeFile.split(".").pop()?.toLowerCase() || "";
  const languageMap: Record<string, string> = {
    c64: "c64py",
    py: "python",
    bas: "basic64",
    asm: "asm",
    asm65: "asm",
    json: "json",
    md: "markdown",
    txt: "plaintext",
    js: "javascript",
    ts: "typescript",
    tsx: "typescript",
    jsx: "javascript",
    css: "css",
    html: "html",
    xml: "xml",
  };

  const language = languageMap[ext] || "plaintext";

  return (
    <div className="flex-1 overflow-hidden">
      <Editor
        height="100%"
        language={language}
        value={fileContents[activeFile] || ""}
        onChange={handleChange}
        onMount={handleEditorMount}
        theme="vs-dark"
        beforeMount={(monaco) => {
          registerC64Languages(monaco);
        }}
        options={{
          fontSize: 13,
          fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: "on",
          lineNumbers: "on",
          renderLineHighlight: "all",
          bracketPairColorization: { enabled: true },
          automaticLayout: true,
          tabSize: 4,
          insertSpaces: false,
          padding: { top: 8, bottom: 8 },
          smoothScrolling: true,
          cursorBlinking: "smooth",
          cursorSmoothCaretAnimation: "on",
          renderWhitespace: "selection",
          guides: {
            bracketPairs: true,
            indentation: true,
          },
        }}
      />
    </div>
  );
}

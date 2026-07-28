import Editor from "@monaco-editor/react";
import { useIDEStore } from "../store/ideStore";

export function EditorPanel() {
  const { activeFile, fileContents, updateFileContent } = useIDEStore();

  if (!activeFile) {
    return (
      <div className="flex-1 flex items-center justify-center bg-editor-bg">
        <div className="text-center">
          <div className="text-6xl mb-4">🖥️</div>
          <h2 className="text-lg font-semibold text-gray-400 mb-2">C64 Intelligence Studio</h2>
          <p className="text-sm text-gray-600">Apri un file o seleziona un plugin dalla barra laterale</p>
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
  };

  const language = languageMap[ext] || "plaintext";

  return (
    <div className="flex-1 overflow-hidden">
      <Editor
        height="100%"
        language={language}
        value={fileContents[activeFile] || ""}
        onChange={(value) => updateFileContent(activeFile, value || "")}
        theme="vs-dark"
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
        }}
      />
    </div>
  );
}

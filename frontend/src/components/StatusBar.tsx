import { useIDEStore } from "../store/ideStore";

export function StatusBar() {
  const { activeFile, isCompiling, activeProject, isFileDirty } = useIDEStore();

  const fileName = activeFile?.split("/").pop() || "";
  const ext = fileName.split(".").pop()?.toUpperCase() || "";
  const dirty = activeFile ? isFileDirty(activeFile) : false;

  const langMap: Record<string, string> = {
    C64: "C64PY",
    PY: "Python",
    BAS: "BASIC V2",
    ASM: "6502 ASM",
    ASM65: "6502 ASM",
    JSON: "JSON",
    MD: "Markdown",
    TXT: "Text",
    JS: "JavaScript",
    TS: "TypeScript",
    TSX: "TypeScript JSX",
    JSX: "JavaScript JSX",
    CSS: "CSS",
    HTML: "HTML",
  };

  return (
    <div className="h-6 bg-editor-accent flex items-center justify-between px-3 text-[11px] text-white select-none">
      <div className="flex items-center gap-3">
        <span className="font-semibold">C64 Intelligence Studio</span>
        {activeProject && (
          <span className="opacity-70">| {activeProject.split("/").pop()}</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        {isCompiling && (
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-yellow-300 rounded-full animate-pulse" />
            Compilazione...
          </span>
        )}
        {dirty && (
          <span className="flex items-center gap-1 opacity-80">
            <span className="w-1.5 h-1.5 bg-yellow-300 rounded-full" />
            Modificato
          </span>
        )}
        {activeFile && (
          <>
            <span className="opacity-70">{fileName}</span>
            {ext && <span className="opacity-50">{langMap[ext] || ext}</span>}
          </>
        )}
        <span className="opacity-50">Commodore 64</span>
      </div>
    </div>
  );
}

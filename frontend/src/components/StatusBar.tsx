import { useIDEStore } from "../store/ideStore";

export function StatusBar() {
  const { activeFile, isCompiling, activeProject } = useIDEStore();

  return (
    <div className="h-6 bg-editor-accent flex items-center justify-between px-3 text-[11px] text-white">
      <div className="flex items-center gap-3">
        <span>C64 Intelligence Studio</span>
        {activeProject && <span className="opacity-70">| {activeProject}</span>}
      </div>
      <div className="flex items-center gap-3">
        {isCompiling && (
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-yellow-300 rounded-full animate-pulse" />
            Compilazione...
          </span>
        )}
        {activeFile && (
          <span className="opacity-70">{activeFile.split("/").pop()}</span>
        )}
        <span className="opacity-50">Commodore 64</span>
      </div>
    </div>
  );
}

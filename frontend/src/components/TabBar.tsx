import { useIDEStore } from "../store/ideStore";

export function TabBar() {
  const { openFiles, activeFile, setActiveFile, closeFile, isFileDirty } = useIDEStore();

  if (openFiles.length === 0) {
    return (
      <div className="h-9 bg-editor-sidebar border-b border-editor-border flex items-center px-3">
        <span className="text-xs text-gray-500 italic">Nessun file aperto</span>
      </div>
    );
  }

  return (
    <div className="h-9 bg-editor-sidebar border-b border-editor-border flex items-end overflow-x-auto">
      {openFiles.map((file) => {
        const isActive = file === activeFile;
        const dirty = isFileDirty(file);
        const name = file.split("/").pop() || file;

        return (
          <div
            key={file}
            onClick={() => setActiveFile(file)}
            className={`group flex items-center gap-1.5 px-3 h-8 cursor-pointer border-r border-editor-border text-xs transition-colors ${
              isActive
                ? "bg-editor-activeTab text-editor-text border-t-2 border-t-editor-accent"
                : "bg-editor-inactiveTab text-gray-400 hover:bg-editor-border/40"
            }`}
          >
            <span className="max-w-[120px] truncate">{name}</span>
            {dirty && <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />}
            <button
              onClick={(e) => {
                e.stopPropagation();
                closeFile(file);
              }}
              className="ml-1 opacity-0 group-hover:opacity-100 hover:text-red-400 transition-opacity"
            >
              ×
            </button>
          </div>
        );
      })}
    </div>
  );
}

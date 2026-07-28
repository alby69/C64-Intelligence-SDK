import { useState, useEffect } from "react";
import { useIDEStore } from "../store/ideStore";
import { openFileDialog, readFile, writeFile } from "../services/tauriBridge";
import { runDiskList, runDiskExtract, runDiskCreate } from "../services/commandService";

interface DiskEntry {
  name: string;
  kind: string;
  size: number;
}

export function DiskBrowser() {
  const { addLog } = useIDEStore.getState();
  const [collapsed, setCollapsed] = useState(true);
  const [imagePath, setImagePath] = useState<string | null>(null);
  const [entries, setEntries] = useState<DiskEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [newDiskName, setNewDiskName] = useState("");
  const [newDiskFormat, setNewDiskFormat] = useState<"d64" | "d81">("d64");

  const handleOpenDisk = async () => {
    try {
      const path = await openFileDialog();
      if (!path) return;
      setImagePath(path);
      setCollapsed(false);
      await loadDisk(path);
    } catch {
      addLog("[DISK] Impossibile aprire file dialog");
    }
  };

  const loadDisk = async (path: string) => {
    setLoading(true);
    setEntries([]);
    try {
      const result = await runDiskList(path);
      // Parse entries from stdout
    } catch {
      addLog("[DISK] Errore nel caricamento disco");
    }
    setLoading(false);
  };

  const handleExtract = async (name: string) => {
    if (!imagePath) return;
    try {
      const outPath = await openFileDialog();
      if (outPath) {
        await runDiskExtract(imagePath, name, outPath);
      }
    } catch {
      addLog("[DISK] Errore estrazione");
    }
  };

  const handleCreateDisk = async () => {
    try {
      const outPath = await openFileDialog();
      if (outPath) {
        await runDiskCreate(outPath, newDiskFormat, newDiskName || "UNTITLED");
        setImagePath(outPath);
        await loadDisk(outPath);
      }
    } catch {
      addLog("[DISK] Errore creazione disco");
    }
  };

  if (collapsed && !imagePath) {
    return (
      <button
        onClick={handleOpenDisk}
        className="fixed bottom-16 right-48 z-50 bg-editor-sidebar border border-editor-border text-editor-text px-3 py-1.5 rounded-full text-xs font-medium shadow-lg hover:border-editor-accent transition-colors"
        title="Disk Browser"
      >
        💾 Disk
      </button>
    );
  }

  return (
    <div className="fixed bottom-16 right-48 z-50 w-80 bg-editor-sidebar border border-editor-border rounded-lg shadow-2xl overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-editor-border bg-editor-bg">
        <span className="text-xs font-semibold text-editor-text uppercase tracking-wider">
          💾 Disk Browser
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={handleOpenDisk}
            className="text-[10px] text-gray-500 hover:text-editor-accent px-1"
            title="Apri disco"
          >
            Apri
          </button>
          <button
            onClick={() => setCollapsed(true)}
            className="text-gray-500 hover:text-editor-text text-xs px-1"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="p-3 space-y-3">
        {imagePath && (
          <div className="text-[11px] text-gray-400 truncate">
            📀 {imagePath.split("/").pop()}
          </div>
        )}

        {loading ? (
          <div className="text-xs text-gray-500 italic text-center py-4">Caricamento...</div>
        ) : entries.length > 0 ? (
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {entries.map((e, i) => (
              <div
                key={i}
                className="flex items-center justify-between px-2 py-1 bg-editor-bg rounded text-xs"
              >
                <div className="flex items-center gap-2 truncate">
                  <span className="text-yellow-400">{e.kind === "PRG" ? "📄" : "📋"}</span>
                  <span className="text-editor-text truncate">{e.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 text-[10px]">{e.size}B</span>
                  <button
                    onClick={() => handleExtract(e.name)}
                    className="text-[10px] text-editor-accent hover:underline"
                  >
                    Estrai
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-xs text-gray-600 mb-3">Nessun disco caricato</p>
            <div className="space-y-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newDiskName}
                  onChange={(e) => setNewDiskName(e.target.value)}
                  placeholder="Nome disco"
                  className="flex-1 bg-editor-bg border border-editor-border rounded px-2 py-1 text-[10px] text-editor-text outline-none"
                />
                <select
                  value={newDiskFormat}
                  onChange={(e) => setNewDiskFormat(e.target.value as "d64" | "d81")}
                  className="bg-editor-bg border border-editor-border rounded px-2 py-1 text-[10px] text-editor-text outline-none"
                >
                  <option value="d64">D64</option>
                  <option value="d81">D81</option>
                </select>
              </div>
              <button
                onClick={handleCreateDisk}
                className="w-full px-2 py-1 bg-editor-accent/20 text-editor-accent text-[10px] rounded hover:bg-editor-accent/30 transition-colors"
              >
                + Crea nuovo disco
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

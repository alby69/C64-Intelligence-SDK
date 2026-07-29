import { useState, useRef, useEffect } from "react";
import { useIDEStore } from "../store/ideStore";
import { openFileDialog } from "../services/tauriBridge";
import { runDiskExtract, runDiskCreate } from "../services/commandService";

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
  const [pos, setPos] = useState({ x: window.innerWidth - 340, y: window.innerHeight - 400 });
  const dragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0, left: 0, top: 0 });

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
      const { execPluginCommand } = await import("../services/pluginService");
      const result = await execPluginCommand("disk-tools", "list", undefined, undefined, [
        "list", path,
      ]);
      if (result.success && result.stdout) {
        const lines = result.stdout.split("\n");
        const parsed: DiskEntry[] = [];
        for (const line of lines) {
          const match = line.match(/\[BASIC\]\s+(.+?)\s{2,}(\w+)\s+(\d+)/);
          if (match) {
            parsed.push({ name: match[1].trim(), kind: match[2], size: parseInt(match[3]) });
          }
        }
        setEntries(parsed);
      }
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

  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).tagName === "INPUT" || (e.target as HTMLElement).tagName === "SELECT") return;
    dragging.current = true;
    dragStart.current = { x: e.clientX, y: e.clientY, left: pos.x, top: pos.y };
    document.body.style.cursor = "grabbing";
    document.body.style.userSelect = "none";
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      setPos({
        x: Math.max(0, dragStart.current.left + (e.clientX - dragStart.current.x)),
        y: Math.max(0, dragStart.current.top + (e.clientY - dragStart.current.y)),
      });
    };
    const handleMouseUp = () => {
      if (dragging.current) {
        dragging.current = false;
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      }
    };
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [pos]);

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
    <div
      className="fixed z-50 w-80 bg-editor-sidebar border border-editor-border rounded-lg shadow-2xl overflow-hidden"
      style={{ left: pos.x, top: pos.y }}
    >
      <div
        className="flex items-center justify-between px-3 py-2 border-b border-editor-border bg-editor-bg cursor-grab"
        onMouseDown={handleMouseDown}
      >
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
            onClick={() => { setCollapsed(true); }}
            className="text-gray-500 hover:text-editor-text text-xs px-1"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="p-3 space-y-3">
        {imagePath && (
          <div className="text-[11px] text-gray-400 truncate">
            📀 {imagePath.split("/").pop() || imagePath.split("\\").pop()}
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

import { useEffect, useState, useCallback } from "react";
import { usePluginStore } from "../store/pluginStore";
import { useIDEStore } from "../store/ideStore";
import { PluginCard } from "./PluginCard";
import { listDirectory, openFileDialog, readFile, DirEntry } from "../services/tauriBridge";

interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  children?: FileNode[];
  expanded?: boolean;
}

function FileTreeItem({
  node,
  depth,
  onFileClick,
}: {
  node: FileNode;
  depth: number;
  onFileClick: (path: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [children, setChildren] = useState<FileNode[]>(node.children || []);

  const toggle = useCallback(async () => {
    if (!node.is_dir) {
      onFileClick(node.path);
      return;
    }
    if (expanded) {
      setExpanded(false);
      return;
    }
    try {
      const entries = await listDirectory(node.path);
      const nodes = entries.map((e) => ({
        name: e.name,
        path: `${node.path}/${e.name}`,
        is_dir: e.is_dir,
      }));
      setChildren(nodes);
      setExpanded(true);
    } catch {
      setExpanded(true);
    }
  }, [node, expanded, onFileClick]);

  const icon = node.is_dir ? (expanded ? "📂" : "📁") : getFileIcon(node.name);

  return (
    <div>
      <div
        onClick={toggle}
        className="flex items-center gap-1 px-2 py-0.5 cursor-pointer hover:bg-editor-border/50 text-xs text-gray-400 hover:text-editor-text transition-colors"
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        <span className="w-4 text-center text-[10px]">
          {node.is_dir ? (expanded ? "▾" : "▸") : ""}
        </span>
        <span className="w-4">{icon}</span>
        <span className="truncate">{node.name}</span>
      </div>
      {expanded &&
        children.map((child) => (
          <FileTreeItem
            key={child.path}
            node={child}
            depth={depth + 1}
            onFileClick={onFileClick}
          />
        ))}
    </div>
  );
}

function getFileIcon(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "c64":
    case "py":
      return "🟦";
    case "bas":
      return "🟩";
    case "asm":
    case "asm65":
      return "🟧";
    case "json":
      return "📋";
    case "md":
    case "txt":
      return "📝";
    case "prg":
      return "💾";
    case "d64":
    case "d81":
      return "💿";
    default:
      return "📄";
  }
}

export function Sidebar() {
  const { plugins, loadPlugins } = usePluginStore();
  const { openFile, activeProject } = useIDEStore();
  const [collapsed, setCollapsed] = useState(false);
  const [tab, setTab] = useState<"files" | "plugins">("files");
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [treeRoot, setTreeRoot] = useState<string>("");

  useEffect(() => {
    loadPlugins();
  }, []);

  useEffect(() => {
    if (activeProject) {
      setTreeRoot(activeProject);
      loadDirectory(activeProject);
    }
  }, [activeProject]);

  const loadDirectory = async (path: string) => {
    try {
      const entries = await listDirectory(path);
      const nodes = entries.map((e) => ({
        name: e.name,
        path: `${path}/${e.name}`,
        is_dir: e.is_dir,
      }));
      setFileTree(nodes);
    } catch {
      setFileTree([]);
    }
  };

  const handleOpenFile = async (filePath: string) => {
    try {
      const content = await readFile(filePath);
      openFile(filePath, content);
    } catch {
      openFile(filePath, "");
    }
  };

  const handleOpenDialog = async () => {
    try {
      const path = await openFileDialog();
      if (path) {
        await handleOpenFile(path);
      }
    } catch {
      // Fallback for browser dev mode
    }
  };

  useEffect(() => {
    const handler = () => handleOpenDialog();
    document.addEventListener("ide:openFile", handler);
    return () => document.removeEventListener("ide:openFile", handler);
  }, []);

  if (collapsed) {
    return (
      <aside className="flex flex-col bg-editor-sidebar border-r border-editor-border w-12">
        <div className="flex items-center justify-center p-2 border-b border-editor-border">
          <button
            onClick={() => setCollapsed(false)}
            className="p-1 hover:bg-editor-border rounded text-editor-text"
            title="Espandi"
          >
            »
          </button>
        </div>
        <div className="flex flex-col items-center gap-2 p-2">
          <button
            onClick={() => { setCollapsed(false); setTab("files"); }}
            className="p-1.5 hover:bg-editor-border rounded text-editor-text text-sm"
            title="File Explorer"
          >
            📁
          </button>
          <button
            onClick={() => { setCollapsed(false); setTab("plugins"); }}
            className="p-1.5 hover:bg-editor-border rounded text-editor-text text-sm"
            title="Plugins"
          >
            🧩
          </button>
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex flex-col bg-editor-sidebar border-r border-editor-border w-64 transition-all duration-200">
      <div className="flex items-center justify-between p-2 border-b border-editor-border">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setTab("files")}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
              tab === "files"
                ? "bg-editor-accent text-white"
                : "text-gray-400 hover:text-editor-text hover:bg-editor-border"
            }`}
          >
            📁 Files
          </button>
          <button
            onClick={() => setTab("plugins")}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
              tab === "plugins"
                ? "bg-editor-accent text-white"
                : "text-gray-400 hover:text-editor-text hover:bg-editor-border"
            }`}
          >
            🧩 Plugins
          </button>
        </div>
        <button
          onClick={() => setCollapsed(true)}
          className="p-1 hover:bg-editor-border rounded text-editor-text"
          title="Comprimi"
        >
          «
        </button>
      </div>

      {tab === "files" && (
        <>
          <div className="flex items-center justify-between px-2 py-1 border-b border-editor-border">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider">
              {treeRoot ? treeRoot.split("/").pop() : "Esplora"}
            </span>
            <button
              onClick={handleOpenDialog}
              className="text-[10px] text-gray-500 hover:text-editor-accent px-1 rounded hover:bg-editor-border"
              title="Apri file (Ctrl+O)"
            >
              + Apri
            </button>
          </div>
          <div className="flex-1 overflow-y-auto py-1">
            {fileTree.length === 0 ? (
              <div className="px-3 py-4 text-center">
                <p className="text-xs text-gray-600">Nessun progetto aperto</p>
                <button
                  onClick={handleOpenDialog}
                  className="mt-2 text-xs text-editor-accent hover:underline"
                >
                  Apri un file...
                </button>
              </div>
            ) : (
              fileTree.map((node) => (
                <FileTreeItem
                  key={node.path}
                  node={node}
                  depth={0}
                  onFileClick={handleOpenFile}
                />
              ))
            )}
          </div>
        </>
      )}

      {tab === "plugins" && (
        <>
          <div className="flex-1 overflow-y-auto p-1 space-y-1">
            {plugins.map((plugin) => (
              <PluginCard key={plugin.name} plugin={plugin} collapsed={collapsed} />
            ))}
          </div>
          <div className="p-2 border-t border-editor-border text-xs text-gray-500">
            {plugins.length} plugin{plugins.length !== 1 ? "i" : ""} caricati
          </div>
        </>
      )}
    </aside>
  );
}

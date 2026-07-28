import { Plugin } from "../store/pluginStore";
import { execPluginCommand } from "../services/pluginService";
import { useIDEStore } from "../store/ideStore";

interface PluginCardProps {
  plugin: Plugin;
  collapsed: boolean;
}

const categoryColors: Record<string, string> = {
  build: "text-yellow-400",
  edit: "text-blue-400",
  tools: "text-green-400",
  run: "text-red-400",
  project: "text-purple-400",
  other: "text-gray-400",
};

const categoryBg: Record<string, string> = {
  build: "bg-yellow-400/10",
  edit: "bg-blue-400/10",
  tools: "bg-green-400/10",
  run: "bg-red-400/10",
  project: "bg-purple-400/10",
  other: "bg-gray-400/10",
};

export function PluginCard({ plugin, collapsed }: PluginCardProps) {
  const { addLog } = useIDEStore.getState();
  const colorClass = categoryColors[plugin.category] || categoryColors.other;
  const bgClass = categoryBg[plugin.category] || categoryBg.other;

  const handleCommand = async (cmdName: string) => {
    addLog(`[PLUGIN] Esecuzione ${plugin.name}::${cmdName}...`);
    const result = await execPluginCommand(plugin.name, cmdName);
    if (result.success) {
      if (result.stdout) {
        result.stdout
          .split("\n")
          .filter(Boolean)
          .forEach((line) => addLog(line));
      }
      addLog(`[OK] ${plugin.name}::${cmdName} completato`);
    } else {
      addLog(`[ERROR] ${result.error || result.stderr}`);
    }
  };

  if (collapsed) {
    return (
      <div
        className="flex items-center justify-center p-2 rounded hover:bg-editor-border cursor-pointer"
        title={`${plugin.name}: ${plugin.description}`}
      >
        <span className="text-lg">{plugin.icon}</span>
      </div>
    );
  }

  return (
    <div className="rounded bg-editor-bg border border-editor-border hover:border-editor-accent/50 p-2 transition-all duration-150 group">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{plugin.icon}</span>
        <span className="text-sm font-medium text-editor-text">{plugin.name}</span>
        <span className={`text-[10px] ml-auto px-1.5 py-0.5 rounded ${bgClass} ${colorClass}`}>
          {plugin.category}
        </span>
      </div>
      <p className="text-[11px] text-gray-500 leading-tight mb-1.5">{plugin.description}</p>
      <div className="flex flex-wrap gap-1">
        {plugin.commands.map((cmd) => (
          <button
            key={cmd.name}
            onClick={() => handleCommand(cmd.name)}
            className="text-[10px] bg-editor-border rounded px-1.5 py-0.5 text-gray-400 hover:text-editor-accent hover:bg-editor-accent/10 transition-colors"
            title={cmd.description}
          >
            {cmd.label}
          </button>
        ))}
      </div>
    </div>
  );
}

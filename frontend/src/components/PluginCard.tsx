import { Plugin } from "../store/pluginStore";

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

export function PluginCard({ plugin, collapsed }: PluginCardProps) {
  const colorClass = categoryColors[plugin.category] || categoryColors.other;

  if (collapsed) {
    return (
      <div
        className="flex items-center justify-center p-2 rounded hover:bg-editor-border cursor-pointer"
        title={`${plugin.description}`}
      >
        <span className="text-lg">{plugin.icon}</span>
      </div>
    );
  }

  return (
    <div className="rounded bg-editor-bg border border-editor-border hover:border-editor-accent p-2 cursor-pointer transition-colors">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{plugin.icon}</span>
        <span className="text-sm font-medium text-editor-text">{plugin.name}</span>
        <span className={`text-[10px] ml-auto ${colorClass}`}>{plugin.category}</span>
      </div>
      <p className="text-[11px] text-gray-500 leading-tight">{plugin.description}</p>
      <div className="mt-1.5 flex flex-wrap gap-1">
        {plugin.commands.map((cmd) => (
          <span
            key={cmd.name}
            className="text-[10px] bg-editor-border rounded px-1.5 py-0.5 text-gray-400 hover:text-editor-accent hover:bg-editor-border/50"
            title={cmd.description}
          >
            {cmd.label}
          </span>
        ))}
      </div>
    </div>
  );
}

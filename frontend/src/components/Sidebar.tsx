import { useEffect, useState } from "react";
import { usePluginStore } from "../store/pluginStore";
import { PluginCard } from "./PluginCard";

export function Sidebar() {
  const { plugins, loadPlugins } = usePluginStore();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    loadPlugins();
  }, []);

  return (
    <aside
      className={`flex flex-col bg-editor-sidebar border-r border-editor-border transition-all duration-200 ${
        collapsed ? "w-12" : "w-64"
      }`}
    >
      <div className="flex items-center justify-between p-2 border-b border-editor-border">
        {!collapsed && (
          <span className="text-xs font-semibold text-editor-text uppercase tracking-wider">
            Plugins
          </span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 hover:bg-editor-border rounded text-editor-text"
          title={collapsed ? "Espandi" : "Comprimi"}
        >
          {collapsed ? "»" : "«"}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-1 space-y-1">
        {plugins.map((plugin) => (
          <PluginCard key={plugin.name} plugin={plugin} collapsed={collapsed} />
        ))}
      </div>

      {!collapsed && (
        <div className="p-2 border-t border-editor-border text-xs text-gray-500">
          {plugins.length} plugin{plugins.length !== 1 ? "s" : ""} caricati
        </div>
      )}
    </aside>
  );
}

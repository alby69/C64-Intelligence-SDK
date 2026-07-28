import { create } from "zustand";

export interface PluginCommand {
  name: string;
  label: string;
  description: string;
  args: string[];
  options: Record<string, any>;
}

export interface Plugin {
  name: string;
  version: string;
  description: string;
  category: string;
  icon: string;
  entry_point: string;
  commands: PluginCommand[];
}

interface PluginState {
  plugins: Plugin[];
  loading: boolean;
  error: string | null;
  loadPlugins: () => Promise<void>;
}

export const usePluginStore = create<PluginState>((set) => ({
  plugins: [],
  loading: false,
  error: null,

  loadPlugins: async () => {
    set({ loading: true, error: null });
    try {
      const { fetchPlugins } = await import("../services/pluginService");
      const plugins = await fetchPlugins();
      set({ plugins, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false, plugins: [] });
    }
  },
}));

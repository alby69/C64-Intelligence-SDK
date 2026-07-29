import { Plugin } from "../store/pluginStore";

const API_BASE = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000/api/v1";

export interface PluginExecResult {
  success: boolean;
  stdout: string;
  stderr: string;
  error?: string;
  returncode?: number;
  output?: {
    messages: { type: string; text: string }[];
    errors: string[];
    files: string[];
    prg_size: number | null;
    load_address: string | null;
    code_address: string | null;
  };
}

export async function fetchPlugins(): Promise<Plugin[]> {
  try {
    const res = await fetch(`${API_BASE}/plugins`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.plugins || [];
  } catch {
    return [];
  }
}

export async function execPluginCommand(
  pluginName: string,
  command: string,
  args?: string[],
  options?: Record<string, any>,
  cliArgs?: string[]
): Promise<PluginExecResult> {
  try {
    const body: Record<string, any> = { command };
    if (args !== undefined) body.args = args;
    if (options !== undefined) body.options = options;
    if (cliArgs !== undefined) body.cli_args = cliArgs;

    const res = await fetch(`${API_BASE}/plugins/${pluginName}/exec`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const result: PluginExecResult = await res.json();

    if (!res.ok) {
      result.success = false;
      result.error = result.error || result.stderr || `HTTP ${res.status}`;
      return result;
    }
    if (!result.success && !result.error) {
      result.error = result.stderr || "Command failed";
    }
    return result;
  } catch (e) {
    return { success: false, stdout: "", stderr: "", error: String(e) };
  }
}

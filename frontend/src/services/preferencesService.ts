import type { UserPreferences } from "./preferencesTypes";

function isTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI__" in window;
}

async function tauriInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T | null> {
  if (!isTauri()) return null;
  try {
    const { invoke } = await import("@tauri-apps/api/tauri");
    return await invoke<T>(cmd, args);
  } catch {
    return null;
  }
}

const DEFAULT_PREFS: UserPreferences = {
  last_project: null,
  last_directory: null,
  theme: "dark",
  font_size: 13,
  window_width: 1280,
  window_height: 800,
  VICE_path: null,
  auto_save: true,
};

export async function loadPreferences(): Promise<UserPreferences> {
  const prefs = await tauriInvoke<UserPreferences>("load_preferences");
  return { ...DEFAULT_PREFS, ...(prefs || {}) };
}

export async function savePreferences(prefs: UserPreferences): Promise<void> {
  if (!isTauri()) return;
  try {
    const { invoke } = await import("@tauri-apps/api/tauri");
    await invoke("save_preferences", { prefs });
  } catch (e) {
    console.error("Failed to save preferences:", e);
  }
}

export async function detectPython(): Promise<string | null> {
  const tauriResult = await tauriInvoke<string>("detect_python");
  if (tauriResult) return tauriResult;
  return navigator.platform.includes("Win") ? "python" : "python3";
}

export async function detectVice(): Promise<string | null> {
  return tauriInvoke<string>("detect_vice");
}

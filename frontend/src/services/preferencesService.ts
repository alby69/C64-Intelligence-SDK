import { invoke } from "@tauri-apps/api/tauri";

export interface UserPreferences {
  last_project: string | null;
  last_directory: string | null;
  theme: string | null;
  font_size: number | null;
  window_width: number | null;
  window_height: number | null;
  VICE_path: string | null;
  auto_save: boolean | null;
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
  try {
    const prefs = await invoke<UserPreferences>("load_preferences");
    return { ...DEFAULT_PREFS, ...prefs };
  } catch {
    return DEFAULT_PREFS;
  }
}

export async function savePreferences(prefs: UserPreferences): Promise<void> {
  try {
    await invoke("save_preferences", { prefs });
  } catch (e) {
    console.error("Failed to save preferences:", e);
  }
}

export async function detectVice(): Promise<string | null> {
  try {
    return await invoke<string | null>("detect_vice");
  } catch {
    return null;
  }
}

export async function detectPython(): Promise<string | null> {
  try {
    return await invoke<string | null>("detect_python");
  } catch {
    return null;
  }
}

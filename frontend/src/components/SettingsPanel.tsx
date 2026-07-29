import { useState, useEffect } from "react";
import {
  loadPreferences,
  savePreferences,
} from "../services/preferencesService";

interface SettingsPanelProps {
  onClose: () => void;
}

export function SettingsPanel({ onClose }: SettingsPanelProps) {
  const [vicePath, setVicePath] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadPreferences().then((p) => setVicePath(p.VICE_path || ""));
  }, []);

  const handleSave = async () => {
    const prefs = await loadPreferences();
    prefs.VICE_path = vicePath || null;
    await savePreferences(prefs);
    setSaved(true);
    setTimeout(onClose, 1000);
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/50 flex items-center justify-center" onClick={onClose}>
      <div className="w-[400px] bg-editor-sidebar border border-editor-border rounded-xl shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="bg-editor-accent px-6 py-4 rounded-t-xl">
          <h1 className="text-white font-bold text-lg">Impostazioni</h1>
        </div>
        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="text-sm text-gray-400 block mb-1">
              Percorso VICE (x64sc)
            </label>
            <input
              type="text"
              value={vicePath}
              onChange={(e) => setVicePath(e.target.value)}
              placeholder="es. C:\Program Files\VICE\x64sc.exe"
              className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded-lg text-sm text-editor-text placeholder-gray-600 focus:outline-none focus:border-editor-accent"
            />
            <p className="text-xs text-gray-600 mt-1">
              Lascia vuoto per usare il comando "x64sc" di default.
            </p>
          </div>
          {saved && (
            <div className="text-green-400 text-sm text-center">✅ Salvato!</div>
          )}
        </div>
        <div className="px-6 py-4 border-t border-editor-border flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
          >
            Annulla
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-editor-accent text-white text-sm font-medium rounded-lg hover:bg-editor-accent/80 transition-colors"
          >
            Salva
          </button>
        </div>
      </div>
    </div>
  );
}

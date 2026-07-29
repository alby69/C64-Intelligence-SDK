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

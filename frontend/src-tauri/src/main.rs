#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::fs;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::io::Write;
use tauri::{Manager, Window};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone)]
struct CommandResult {
    success: bool,
    stdout: String,
    stderr: String,
    code: i32,
}

#[derive(Serialize, Deserialize, Clone)]
struct DirEntry {
    name: String,
    is_dir: bool,
    size: u64,
}

#[derive(Serialize, Deserialize, Clone, Default)]
struct UserPreferences {
    last_project: Option<String>,
    last_directory: Option<String>,
    theme: Option<String>,
    font_size: Option<u32>,
    window_width: Option<u32>,
    window_height: Option<u32>,
   VICE_path: Option<String>,
    auto_save: Option<bool>,
}

fn prefs_path() -> PathBuf {
    let mut p = dirs::config_dir().unwrap_or_else(|| PathBuf::from("."));
    p.push("c64-intelligence-studio");
    fs::create_dir_all(&p).ok();
    p.push("preferences.json");
    p
}

#[tauri::command]
fn load_preferences() -> UserPreferences {
    let path = prefs_path();
    if path.exists() {
        if let Ok(data) = fs::read_to_string(&path) {
            if let Ok(prefs) = serde_json::from_str::<UserPreferences>(&data) {
                return prefs;
            }
        }
    }
    UserPreferences::default()
}

#[tauri::command]
fn save_preferences(prefs: UserPreferences) -> Result<(), String> {
    let path = prefs_path();
    let json = serde_json::to_string_pretty(&prefs).map_err(|e| e.to_string())?;
    fs::write(&path, json).map_err(|e| e.to_string())
}

#[tauri::command]
fn run_command(program: String, args: Vec<String>, cwd: Option<String>) -> CommandResult {
    let mut cmd = Command::new(&program);
    cmd.args(&args);
    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    if let Some(dir) = cwd {
        cmd.current_dir(dir);
    }

    match cmd.output() {
        Ok(output) => CommandResult {
            success: output.status.success(),
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
            code: output.status.code().unwrap_or(-1),
        },
        Err(e) => CommandResult {
            success: false,
            stdout: String::new(),
            stderr: e.to_string(),
            code: -1,
        },
    }
}

#[tauri::command]
fn read_file(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path).map_err(|e| e.to_string())
}

#[tauri::command]
fn write_file(path: String, content: String) -> Result<(), String> {
    std::fs::write(&path, content).map_err(|e| e.to_string())
}

#[tauri::command]
fn list_directory(path: String) -> Result<Vec<DirEntry>, String> {
    let entries = std::fs::read_dir(&path).map_err(|e| e.to_string())?;
    let mut result = Vec::new();

    for entry in entries.flatten() {
        let metadata = entry.metadata().ok();
        result.push(DirEntry {
            name: entry.file_name().to_string_lossy().to_string(),
            is_dir: metadata.as_ref().map_or(false, |m| m.is_dir()),
            size: metadata.as_ref().map_or(0, |m| m.len()),
        });
    }

    result.sort_by(|a, b| {
        if a.is_dir == b.is_dir {
            a.name.to_lowercase().cmp(&b.name.to_lowercase())
        } else {
            b.is_dir.cmp(&a.is_dir)
        }
    });

    Ok(result)
}

#[tauri::command]
fn open_file_dialog(window: Window) -> Option<String> {
    use rfd::FileDialog;

    FileDialog::new()
        .set_parent(Some(&window))
        .add_filter("C64 Source", &["c64", "bas", "asm", "asm65"])
        .add_filter("Project", &["c64proj"])
        .add_filter("All Files", &["*"])
        .pick_file()
        .map(|p| p.to_string_lossy().to_string())
}

#[tauri::command]
fn save_file_dialog(window: Window, default_name: Option<String>) -> Option<String> {
    use rfd::FileDialog;

    let mut dialog = FileDialog::new()
        .set_parent(Some(&window))
        .add_filter("C64 Source", &["c64"])
        .add_filter("BASIC", &["bas"])
        .add_filter("Assembly", &["asm"])
        .add_filter("Project", &["c64proj"]);

    if let Some(name) = default_name {
        dialog = dialog.set_file_name(&name);
    }

    dialog.save_file().map(|p| p.to_string_lossy().to_string())
}

#[tauri::command]
fn detect_vice() -> Option<String> {
    let vice_dirs = [
        "/usr/local/bin/x64sc",
        "/usr/bin/x64sc",
        "/usr/local/share/vice",
        "/usr/share/vice",
    ];

    for d in &vice_dirs {
        if std::path::Path::new(d).exists() {
            return Some(d.to_string());
        }
    }

    // Try which
    if let Ok(output) = Command::new("which").arg("x64sc").output() {
        if output.status.success() {
            let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if !path.is_empty() {
                return Some(path);
            }
        }
    }

    None
}

#[tauri::command]
fn detect_python() -> Option<String> {
    let python_names = ["python3", "python"];
    for name in &python_names {
        if let Ok(output) = Command::new(name).arg("--version").output() {
            if output.status.success() {
                return Some(name.to_string());
            }
        }
    }
    None
}

#[tauri::command]
fn start_backend_services(app_handle: tauri::AppHandle) {
    println!("Inizializzazione dei servizi di backend C64...");

    // Check for Python
    match detect_python() {
        Some(p) => println!("Python found: {}", p),
        None => println!("WARNING: Python not found. Plugin system may not work."),
    }

    // Check for VICE
    match detect_vice() {
        Some(v) => println!("VICE found: {}", v),
        None => println!("WARNING: VICE emulator not found. Emulator plugin may not work."),
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            start_backend_services,
            run_command,
            read_file,
            write_file,
            list_directory,
            open_file_dialog,
            save_file_dialog,
            load_preferences,
            save_preferences,
            detect_vice,
            detect_python,
        ])
        .setup(|app| {
            // Restore window state from preferences
            let prefs = load_preferences();
            if let Some(window) = app.get_window("main") {
                if let (Some(w), Some(h)) = (prefs.window_width, prefs.window_height) {
                    let _ = window.set_size(tauri::PhysicalSize::new(w, h));
                }
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("errore durante l'esecuzione dell'applicazione tauri");
}

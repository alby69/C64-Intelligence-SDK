#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Stdio};
use std::io::Write;
use tauri::{Manager, Window};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
struct CommandResult {
    success: bool,
    stdout: String,
    stderr: String,
    code: i32,
}

#[derive(Serialize, Deserialize)]
struct DirEntry {
    name: String,
    is_dir: bool,
    size: u64,
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
        .add_filter("Assembly", &["asm"]);

    if let Some(name) = default_name {
        dialog = dialog.set_file_name(&name);
    }

    dialog.save_file().map(|p| p.to_string_lossy().to_string())
}

#[tauri::command]
fn start_backend_services(app_handle: tauri::AppHandle) {
    println!("Inizializzazione dei servizi di backend C64...");
    let _ = app_handle;
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
        ])
        .run(tauri::generate_context!())
        .expect("errore durante l'esecuzione dell'applicazione tauri");
}

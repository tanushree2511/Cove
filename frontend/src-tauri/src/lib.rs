use std::sync::{Arc, Mutex};
use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};

struct SidecarState(Arc<Mutex<Vec<CommandChild>>>);

fn free_port(port: &str) {
    #[cfg(unix)]
    {
        let _ = std::process::Command::new("fuser")
            .args(["-k", "-9", &format!("{}/tcp", port)])
            .output();
    }
    #[cfg(windows)]
    {
        // Find and kill the PID using the port
        if let Ok(out) = std::process::Command::new("cmd")
            .args(["/C", &format!("for /f \"tokens=5\" %a in ('netstat -ano ^| findstr :{} ^| findstr LISTENING') do taskkill /F /PID %a", port)])
            .output()
        {
            let _ = out;
        }
    }
}

fn spawn_sidecar(
    app: &tauri::App,
    name: &str,
    port: &str,
    extra_envs: &[(&str, &str)],
    tmp_dir: &std::path::Path,
    children: Arc<Mutex<Vec<CommandChild>>>,
) {
    match app.shell().sidecar(name) {
        Ok(mut cmd) => {
            // PyInstaller one-file apps unpack to the temp dir: point every platform's variable at ours so the stale
            // _MEI* cleanup in setup() actually covers it (TMPDIR is Unix, TEMP/TMP are Windows).
            cmd = cmd
                .env("COVE_PORT", port)
                .env("TMPDIR", tmp_dir)
                .env("TEMP", tmp_dir)
                .env("TMP", tmp_dir);
            for (k, v) in extra_envs {
                cmd = cmd.env(k, v);
            }
            log::info!("Spawning {} sidecar on port {}...", name, port);
            match cmd.spawn() {
                Ok((mut receiver, child)) => {
                    if let Ok(mut guard) = children.lock() {
                        guard.push(child);
                    }
                    let sidecar_name = name.to_string();
                    tauri::async_runtime::spawn(async move {
                        while let Some(event) = receiver.recv().await {
                            match event {
                                CommandEvent::Stdout(line) => {
                                    let msg = String::from_utf8_lossy(&line);
                                    log::info!("[{}] {}", sidecar_name, msg.trim_end());
                                }
                                CommandEvent::Stderr(line) => {
                                    let msg = String::from_utf8_lossy(&line);
                                    log::warn!("[{}] {}", sidecar_name, msg.trim_end());
                                }
                                CommandEvent::Error(err) => {
                                    log::error!("[{} ERROR] {}", sidecar_name, err);
                                }
                                CommandEvent::Terminated(status) => {
                                    log::warn!("[{} Terminated] code: {:?}", sidecar_name, status.code);
                                }
                                _ => {}
                            }
                        }
                    });
                }
                Err(e) => {
                    log::error!("Failed to spawn {}: {}", name, e);
                }
            }
        }
        Err(e) => {
            log::error!("Sidecar '{}' not found: {}", name, e);
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let children: Arc<Mutex<Vec<CommandChild>>> = Arc::new(Mutex::new(Vec::new()));
    let children_setup = children.clone();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(
            tauri_plugin_log::Builder::default()
                .level(log::LevelFilter::Info)
                .build(),
        )
        .setup(move |app| {
            log::info!("Cove Desktop initializing...");
            app.manage(SidecarState(children_setup.clone()));

            // Resolve data + tmp dirs
            let home = std::env::var("HOME")
                .or_else(|_| std::env::var("USERPROFILE"))
                .unwrap_or_else(|_| "/tmp".to_string());
            let config_base = if cfg!(target_os = "macos") {
                std::path::PathBuf::from(&home).join("Library").join("Application Support")
            } else if cfg!(windows) {
                std::env::var("APPDATA")
                    .map(std::path::PathBuf::from)
                    .unwrap_or_else(|_| std::path::PathBuf::from(&home))
            } else {
                std::path::PathBuf::from(&home).join(".config")
            };
            let data_dir = config_base.join("Cove");
            let tmp_dir = data_dir.join("tmp");
            let _ = std::fs::create_dir_all(&tmp_dir);

            // Clean stale PyInstaller _MEI dirs
            for base in [tmp_dir.as_path(), std::path::Path::new("/tmp")] {
                if let Ok(entries) = std::fs::read_dir(base) {
                    for entry in entries.flatten() {
                        if entry.file_name().to_string_lossy().starts_with("_MEI") {
                            let _ = std::fs::remove_dir_all(entry.path());
                        }
                    }
                }
            }

            // Kill stale processes on our ports
            free_port("8000");
            free_port("8001");
            std::thread::sleep(std::time::Duration::from_millis(200));

            let data_str = data_dir.to_string_lossy().to_string();

            // The CLIP + face models are bundled once as a Tauri resource (<resource_dir>/models); both backends
            // read them from there. In `tauri dev` the folder is absent and the backends fall back to ./models.
            let model_str = app
                .path()
                .resource_dir()
                .map(|d| d.join("models").to_string_lossy().to_string())
                .unwrap_or_default();
            let envs: Vec<(&str, &str)> = vec![
                ("COVE_USER_DATA", data_str.as_str()),
                ("COVE_MODEL_DIR", model_str.as_str()),
            ];

            // Spawn cove-backend (photo API, port 8000)
            spawn_sidecar(
                app,
                "cove-backend",
                "8000",
                &envs,
                &tmp_dir,
                children_setup.clone(),
            );

            // Spawn video-backend (video API, port 8001)
            spawn_sidecar(
                app,
                "video-backend",
                "8001",
                &envs,
                &tmp_dir,
                children_setup.clone(),
            );

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(move |app_handle, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(state) = app_handle.try_state::<SidecarState>() {
                    if let Ok(mut guard) = state.0.lock() {
                        for child in guard.drain(..) {
                            log::info!("Terminating sidecar on exit...");
                            let _ = child.kill();
                        }
                    }
                }
            }
        });
}

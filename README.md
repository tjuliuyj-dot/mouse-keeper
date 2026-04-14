# 🖱️ Mouse Keeper

**防止屏幕休眠工具** — A lightweight Windows utility that prevents your screen from sleeping by simulating imperceptible mouse micro-movements.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- **Invisible mouse movements** — Moves the cursor 1px right then 1px left, completely imperceptible
- **Windows API integration** — Uses `SetThreadExecutionState` for reliable sleep prevention
- **Real-time idle monitoring** — Displays system idle time to confirm it's working
- **Modern dark UI** — Clean tkinter interface with animated pulse ring
- **Configurable interval** — Adjust simulation frequency from 5s to 120s
- **Activity log** — Timestamped event log for tracking all simulation events
- **Zero clicks** — Only simulates movement, never triggers mouse clicks

## 📸 Screenshot

<!-- Add a screenshot here after running the app -->

## 🚀 Quick Start

### Requirements

- Python 3.7+
- Windows OS
- No additional packages needed (uses only standard library + `ctypes`)

### Run

```bash
python mouse_keeper.py
```

### Create Desktop Shortcut

```powershell
powershell -ExecutionPolicy Bypass -File create_shortcut.ps1
```

## 📁 Project Structure

```
mouseclick/
├── mouse_keeper.py       # Main application (GUI + logic)
├── create_shortcut.ps1   # PowerShell script to create desktop shortcut
├── .gitignore
└── README.md
```

## 🛠️ How It Works

1. Uses Windows `SendInput` API to generate tiny mouse movements (±1 pixel)
2. Calls `SetThreadExecutionState` to tell Windows to keep the display on
3. Monitors system idle time via `GetLastInputInfo` API
4. After each simulation, idle time resets to ~0s, proving the prevention is active

## ⚙️ Configuration

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| Interval | 5–120s | 30s | Time between mouse simulations |

## 📜 License

MIT License — feel free to use and modify.

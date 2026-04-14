# 🖱️ Mouse Keeper

A lightweight Windows utility that prevents your screen from sleeping by simulating imperceptible mouse micro-movements.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- **Invisible mouse movements** — Moves the cursor 1px right then 1px left, completely imperceptible
- **Windows API integration** — Uses `SetThreadExecutionState` for reliable sleep prevention
- **Real-time idle monitoring** — Displays system idle time to confirm it's working
- **Modern dark UI** — Clean tkinter interface with animated pulse ring and activity log
- **Configurable interval** — Adjust simulation frequency from 5s to 120s via slider
- **Zero clicks** — Only simulates movement, never triggers mouse clicks or interferes with your work

## 🚀 Quick Start

### Requirements

- Python 3.7+
- Windows OS
- No additional packages required (uses only the standard library)

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
├── create_shortcut.ps1   # PowerShell script to create a desktop shortcut
├── .gitignore
└── README.md
```

## 🛠️ How It Works

1. **`SendInput` API** — Generates tiny relative mouse movements (±1 pixel) that are invisible to the user
2. **`SetThreadExecutionState`** — Tells Windows to keep the display and system awake
3. **`GetLastInputInfo`** — Monitors system idle time in real-time; after each simulation the idle timer resets to ~0s, proving the prevention is active

## ⚙️ Configuration

| Setting  | Range    | Default | Description                        |
|----------|----------|---------|------------------------------------|
| Interval | 5 – 120s | 30s     | Time between mouse simulations     |

## 📜 License

MIT License — feel free to use and modify.

"""
Mouse Keeper - 屏幕保持唤醒工具
Simulates mouse micro-movements to prevent screen from sleeping.
The movements are imperceptible and won't interfere with your work.
Uses Windows SetThreadExecutionState API for reliable sleep prevention.
"""

import tkinter as tk
from tkinter import font as tkfont
import ctypes
import ctypes.wintypes
import threading
import time
import math
import sys
import subprocess
from datetime import datetime

# ─── Windows API Constants ───────────────────────────────────────────────────
ES_CONTINUOUS        = 0x80000000
ES_SYSTEM_REQUIRED   = 0x00000001
ES_DISPLAY_REQUIRED  = 0x00000002

# For SendInput mouse simulation
INPUT_MOUSE    = 0
MOUSEEVENTF_MOVE = 0x0001

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("_input", _INPUT),
    ]

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.UINT),
        ("dwTime", ctypes.wintypes.DWORD),
    ]

def get_idle_seconds():
    """Get the number of seconds since the last user input (keyboard/mouse)."""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0

def send_mouse_move(dx=0, dy=0):
    """Send a relative mouse movement via Windows SendInput API."""
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp._input.mi.dx = dx
    inp._input.mi.dy = dy
    inp._input.mi.mouseData = 0
    inp._input.mi.dwFlags = MOUSEEVENTF_MOVE
    inp._input.mi.time = 0
    inp._input.mi.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def set_keep_awake(enable: bool):
    """Enable or disable the Windows keep-awake flag."""
    if enable:
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )
    else:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

def get_screen_timeout():
    """Query the current screen off timeout from Windows power settings."""
    try:
        result = subprocess.run(
            ["powercfg", "/query", "SCHEME_CURRENT", "SUB_VIDEO", "VIDEOIDLE"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split('\n'):
            if 'Current AC Power Setting Index' in line:
                hex_val = line.strip().split('0x')[-1]
                seconds = int(hex_val, 16)
                if seconds == 0:
                    return "从不"
                minutes = seconds // 60
                return f"{minutes} 分钟"
        return "未知"
    except Exception:
        return "未知"

# ─── Color Palette ───────────────────────────────────────────────────────────
COLORS = {
    "bg_dark":      "#0f1117",
    "bg_card":      "#1a1d27",
    "bg_card_alt":  "#222633",
    "accent":       "#6c63ff",
    "accent_hover": "#857dff",
    "accent_glow":  "#6c63ff",
    "success":      "#2dd4a8",
    "warning":      "#fbbf24",
    "danger":       "#f87171",
    "flash":        "#44ff88",
    "flash_bg":     "#1a3a2a",
    "text":         "#e8eaed",
    "text_dim":     "#8b8fa3",
    "text_muted":   "#5a5e72",
    "border":       "#2a2e3d",
    "ring_bg":      "#252940",
    "ring_track":   "#3a3f55",
    "log_bg":       "#13151e",
    "log_text":     "#7ec8a0",
}

class PulseRing(tk.Canvas):
    """Animated ring that pulses when active."""

    def __init__(self, parent, size=180, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=COLORS["bg_card"], highlightthickness=0, **kwargs)
        self.size = size
        self.cx = size // 2
        self.cy = size // 2
        self.angle = 0
        self.pulse_phase = 0
        self.active = False
        self.flash_step = 0
        self._draw_static()

    def _draw_static(self):
        self.delete("all")
        r = self.size // 2 - 15
        # Background ring
        self.create_oval(
            self.cx - r, self.cy - r, self.cx + r, self.cy + r,
            outline=COLORS["ring_track"], width=6, tags="bg_ring"
        )
        # Status text
        self.status_text = self.create_text(
            self.cx, self.cy - 10,
            text="就绪", font=("Segoe UI", 14, "bold"),
            fill=COLORS["text_dim"], tags="status"
        )
        self.time_text = self.create_text(
            self.cx, self.cy + 18,
            text="00:00:00", font=("Consolas", 20, "bold"),
            fill=COLORS["text"], tags="timer"
        )

    def set_active(self, active: bool):
        self.active = active
        if active:
            self.itemconfig("status", text="运行中", fill=COLORS["success"])
        else:
            self.itemconfig("status", text="已停止", fill=COLORS["text_dim"])
            self._draw_static_arc()

    def _draw_static_arc(self):
        self.delete("arc")
        self.delete("flash_ring")

    def update_timer(self, seconds: int):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        self.itemconfig("timer", text=f"{h:02d}:{m:02d}:{s:02d}")

    def flash(self):
        """Trigger a bright flash effect on the ring to indicate a simulation event."""
        self.flash_step = 8
        self._animate_flash()

    def _animate_flash(self):
        """Animate the flash: bright ring that fades out."""
        if self.flash_step <= 0:
            self.delete("flash_ring")
            return
        r = self.size // 2 - 15
        intensity = self.flash_step / 8.0
        g = int(0x44 + (0xff - 0x44) * intensity)
        color = f"#{0x44:02x}{g:02x}{int(0x88 + (0xff - 0x88) * intensity):02x}"
        width = int(6 + 6 * intensity)

        self.delete("flash_ring")
        self.create_oval(
            self.cx - r - 2, self.cy - r - 2, self.cx + r + 2, self.cy + r + 2,
            outline=color, width=width, tags="flash_ring"
        )
        self.flash_step -= 1
        self.after(60, self._animate_flash)

    def animate(self):
        if not self.active:
            return
        self.delete("arc")
        r = self.size // 2 - 15
        self.angle = (self.angle + 4) % 360
        self.pulse_phase += 0.08

        # Draw animated arc
        self.create_arc(
            self.cx - r, self.cy - r, self.cx + r, self.cy + r,
            start=self.angle, extent=120,
            outline=COLORS["success"], width=6,
            style="arc", tags="arc"
        )
        # Second arc for visual richness
        self.create_arc(
            self.cx - r, self.cy - r, self.cx + r, self.cy + r,
            start=(self.angle + 200) % 360, extent=80,
            outline=COLORS["accent"], width=4,
            style="arc", tags="arc"
        )

        self.after(30, self.animate)


class MouseKeeperApp:
    """Main application class."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mouse Keeper - 屏幕保持唤醒")
        self.root.configure(bg=COLORS["bg_dark"])
        self.root.resizable(False, False)

        # Window size and centering
        win_w, win_h = 440, 820
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")

        # Try to set icon (silently fail if not available)
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        # State
        self.running = False
        self.worker_thread = None
        self.elapsed_seconds = 0
        self.click_count = 0
        self.interval = 30  # seconds between simulations
        self.countdown = 0  # countdown to next simulation
        self.screen_timeout_str = get_screen_timeout()

        self._build_ui()
        self._update_clock()
        self._update_idle_monitor()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self.root, bg=COLORS["bg_dark"])
        header.pack(fill="x", pady=(16, 0))

        tk.Label(
            header, text="🖱️  Mouse Keeper",
            font=("Segoe UI", 22, "bold"),
            fg=COLORS["text"], bg=COLORS["bg_dark"]
        ).pack()
        tk.Label(
            header, text="防止屏幕休眠 · 模拟鼠标微移动",
            font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"]
        ).pack(pady=(2, 0))

        # ── Pulse Ring ──
        ring_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        ring_frame.pack(pady=(12, 6))
        self.pulse_ring = PulseRing(ring_frame, size=200)
        self.pulse_ring.pack()

        # ── System Monitor Cards ──
        monitor_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        monitor_frame.pack(fill="x", padx=25, pady=(6, 4))

        # Idle time card
        idle_card = tk.Frame(monitor_frame, bg=COLORS["bg_card"], padx=10, pady=6)
        idle_card.grid(row=0, column=0, padx=3, sticky="nsew")
        monitor_frame.columnconfigure(0, weight=1)
        tk.Label(idle_card, text="⏱ 系统空闲时间", font=("Segoe UI", 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg_card"]).pack()
        self.idle_label = tk.Label(idle_card, text="0 秒", font=("Segoe UI", 13, "bold"),
                                   fg=COLORS["warning"], bg=COLORS["bg_card"])
        self.idle_label.pack()

        # Countdown card
        cd_card = tk.Frame(monitor_frame, bg=COLORS["bg_card"], padx=10, pady=6)
        cd_card.grid(row=0, column=1, padx=3, sticky="nsew")
        monitor_frame.columnconfigure(1, weight=1)
        tk.Label(cd_card, text="⏳ 下次模拟", font=("Segoe UI", 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg_card"]).pack()
        self.countdown_label = tk.Label(cd_card, text="--", font=("Segoe UI", 13, "bold"),
                                         fg=COLORS["accent"], bg=COLORS["bg_card"])
        self.countdown_label.pack()

        # Screen timeout card
        to_card = tk.Frame(monitor_frame, bg=COLORS["bg_card"], padx=10, pady=6)
        to_card.grid(row=0, column=2, padx=3, sticky="nsew")
        monitor_frame.columnconfigure(2, weight=1)
        tk.Label(to_card, text="🖥 屏幕超时", font=("Segoe UI", 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg_card"]).pack()
        tk.Label(to_card, text=self.screen_timeout_str, font=("Segoe UI", 13, "bold"),
                 fg=COLORS["text"], bg=COLORS["bg_card"]).pack()

        # ── Info label ──
        info_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        info_frame.pack(fill="x", padx=25, pady=(2, 2))
        self.idle_info = tk.Label(
            info_frame,
            text="💡 空闲时间在每次模拟后会重置为 0，证明防休眠有效",
            font=("Segoe UI", 8), fg=COLORS["text_muted"], bg=COLORS["bg_dark"],
            wraplength=380, justify="left"
        )
        self.idle_info.pack(anchor="w")

        # ── Stats Cards ──
        stats_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        stats_frame.pack(fill="x", padx=40, pady=(6, 4))

        self._build_stat_card(stats_frame, "模拟次数", "click_label", "0", 0)
        self._build_stat_card(stats_frame, "间隔 (秒)", "interval_label",
                              str(self.interval), 1)
        self._build_stat_card(stats_frame, "状态", "status_label", "待机", 2)

        # ── Interval Slider ──
        slider_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        slider_frame.pack(fill="x", padx=40, pady=(6, 4))

        tk.Label(
            slider_frame, text="模拟间隔",
            font=("Segoe UI", 9),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"]
        ).pack(anchor="w")

        self.interval_slider = tk.Scale(
            slider_frame, from_=5, to=120, orient="horizontal",
            bg=COLORS["bg_card"], fg=COLORS["text"],
            troughcolor=COLORS["ring_track"],
            activebackground=COLORS["accent"],
            highlightthickness=0, bd=0,
            sliderlength=20, length=340,
            font=("Consolas", 9),
            command=self._on_interval_change
        )
        self.interval_slider.set(self.interval)
        self.interval_slider.pack(fill="x")

        tk.Label(
            slider_frame, text="5s ────────────────────────── 120s",
            font=("Consolas", 8),
            fg=COLORS["text_muted"], bg=COLORS["bg_dark"]
        ).pack(fill="x")

        # ── Control Buttons ──
        btn_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        btn_frame.pack(pady=(10, 6))

        self.start_btn = tk.Button(
            btn_frame, text="▶  开始", font=("Segoe UI", 13, "bold"),
            fg="#ffffff", bg=COLORS["accent"],
            activebackground=COLORS["accent_hover"],
            activeforeground="#ffffff",
            relief="flat", cursor="hand2",
            width=14, height=1,
            command=self._toggle
        )
        self.start_btn.pack(pady=5)

        # ── Event Log ──
        log_header = tk.Frame(self.root, bg=COLORS["bg_dark"])
        log_header.pack(fill="x", padx=20, pady=(4, 2))
        tk.Label(
            log_header, text="📋 活动日志",
            font=("Segoe UI", 10, "bold"),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"]
        ).pack(anchor="w")

        log_container = tk.Frame(self.root, bg=COLORS["border"], padx=1, pady=1)
        log_container.pack(fill="both", expand=True, padx=20, pady=(0, 4))

        self.log_text = tk.Text(
            log_container, height=5,
            bg=COLORS["log_bg"], fg=COLORS["log_text"],
            font=("Consolas", 9),
            relief="flat", bd=0, padx=8, pady=6,
            wrap="word", state="disabled",
            insertbackground=COLORS["log_text"],
            selectbackground=COLORS["accent"],
        )
        self.log_text.pack(fill="both", expand=True)

        # Configure text tags for colored log entries
        self.log_text.tag_configure("time", foreground="#6c7a9a")
        self.log_text.tag_configure("event", foreground=COLORS["flash"])
        self.log_text.tag_configure("info", foreground=COLORS["text_dim"])
        self.log_text.tag_configure("start", foreground=COLORS["success"])
        self.log_text.tag_configure("stop", foreground=COLORS["danger"])
        self.log_text.tag_configure("idle_reset", foreground=COLORS["warning"])

        # ── Footer ──
        tk.Label(
            self.root,
            text="鼠标微移动 · 不影响正常使用 · 零点击",
            font=("Segoe UI", 8),
            fg=COLORS["text_muted"], bg=COLORS["bg_dark"]
        ).pack(side="bottom", pady=(0, 8))

    def _log(self, message, tag="info"):
        """Add a timestamped entry to the event log."""
        now = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{now}] ", "time")
        self.log_text.insert("end", f"{message}\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _build_stat_card(self, parent, label, attr_name, value, col):
        card = tk.Frame(parent, bg=COLORS["bg_card"], padx=12, pady=6)
        card.grid(row=0, column=col, padx=4, sticky="nsew")
        parent.columnconfigure(col, weight=1)

        tk.Label(
            card, text=label, font=("Segoe UI", 8),
            fg=COLORS["text_dim"], bg=COLORS["bg_card"]
        ).pack()
        lbl = tk.Label(
            card, text=value, font=("Segoe UI", 14, "bold"),
            fg=COLORS["text"], bg=COLORS["bg_card"]
        )
        lbl.pack()
        setattr(self, attr_name, lbl)

    def _on_interval_change(self, val):
        self.interval = int(val)
        self.interval_label.config(text=str(self.interval))

    def _toggle(self):
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self.running = True
        self.elapsed_seconds = 0
        self.click_count = 0
        self.countdown = self.interval

        # UI updates
        self.start_btn.config(
            text="⏹  停止", bg=COLORS["danger"],
            activebackground="#fb9a9a"
        )
        self.status_label.config(text="活跃", fg=COLORS["success"])
        self.click_label.config(text="0")
        self.pulse_ring.set_active(True)
        self.pulse_ring.animate()
        self.interval_slider.config(state="disabled")

        # Enable keep-awake via Windows API
        set_keep_awake(True)

        # Log start event
        self._log(f"▶ 开始运行 (间隔: {self.interval}秒)", "start")
        self._log(f"ℹ 屏幕超时设置: {self.screen_timeout_str}", "info")

        # Start worker thread
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _stop(self):
        self.running = False
        self.countdown = 0

        # UI updates
        self.start_btn.config(
            text="▶  开始", bg=COLORS["accent"],
            activebackground=COLORS["accent_hover"]
        )
        self.status_label.config(text="待机", fg=COLORS["text"])
        self.pulse_ring.set_active(False)
        self.interval_slider.config(state="normal")
        self.countdown_label.config(text="--")

        # Disable keep-awake
        set_keep_awake(False)

        # Log stop event
        self._log(f"⏹ 已停止 (共模拟 {self.click_count} 次)", "stop")

    def _worker(self):
        """Background thread that periodically simulates mouse micro-movement."""
        while self.running:
            self.countdown = self.interval
            # Wait for the interval, checking every second to allow quick stop
            for i in range(self.interval):
                if not self.running:
                    return
                time.sleep(1)
                self.countdown = self.interval - i - 1

            if not self.running:
                return

            # Simulate invisible mouse movement: move 1px right, then 1px left
            send_mouse_move(1, 0)
            time.sleep(0.05)
            send_mouse_move(-1, 0)

            self.click_count += 1
            # Schedule UI update on main thread
            self.root.after(0, self._on_simulation_event)

    def _on_simulation_event(self):
        """Called on the main thread after each simulation event."""
        # Update click count
        if hasattr(self, 'click_label'):
            self.click_label.config(text=str(self.click_count))

        # Flash the ring for visual feedback
        self.pulse_ring.flash()

        # Log the event
        idle = get_idle_seconds()
        self._log(
            f"✦ 第 {self.click_count} 次模拟完成 (空闲已重置: {idle:.1f}秒)",
            "event"
        )

    def _update_idle_monitor(self):
        """Update the system idle time display every 500ms."""
        idle = get_idle_seconds()

        if idle < 1:
            idle_text = "< 1 秒"
            color = COLORS["success"]
        elif idle < 10:
            idle_text = f"{idle:.0f} 秒"
            color = COLORS["success"]
        elif idle < 60:
            idle_text = f"{idle:.0f} 秒"
            color = COLORS["warning"]
        else:
            minutes = idle / 60
            idle_text = f"{minutes:.1f} 分"
            color = COLORS["danger"]

        self.idle_label.config(text=idle_text, fg=color)

        # Update countdown
        if self.running and self.countdown > 0:
            self.countdown_label.config(text=f"{self.countdown} 秒")
        elif not self.running:
            self.countdown_label.config(text="--")

        self.root.after(500, self._update_idle_monitor)

    def _update_clock(self):
        """Update the elapsed time display every second."""
        if self.running:
            self.elapsed_seconds += 1
            self.pulse_ring.update_timer(self.elapsed_seconds)
        self.root.after(1000, self._update_clock)

    def _on_close(self):
        """Clean shutdown."""
        self.running = False
        set_keep_awake(False)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MouseKeeperApp()
    app.run()

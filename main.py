import calendar
import ctypes
import os
import sqlite3
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable
from tkinter import ttk

try:
    from PIL import Image, ImageFilter, ImageTk
except Exception:
    Image = None
    ImageFilter = None
    ImageTk = None

APP_NAME = "DailyTodo"
APP_DATA_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
DB_PATH = APP_DATA_DIR / "todo_app.db"
WINDOW_TITLE = "Daily To Do"
BACKGROUND_PID_FILE = APP_DATA_DIR / "background.pid"
BACKGROUND_HEARTBEAT_FILE = APP_DATA_DIR / "background.heartbeat"
TIME_FORMAT = "%H:%M"
CHECK_INTERVAL_MS = 1000
BACKGROUND_STALE_SECONDS = 90
BACKGROUND_FLAG = "--background"
REPEAT_OPTIONS = ["Once", "Daily", "Weekly", "Monthly", "Annually"]
REPEAT_TO_RULE = {
    "Once": "once",
    "Daily": "daily",
    "Weekly": "weekly",
    "Monthly": "monthly",
    "Annually": "annually",
}
RULE_TO_REPEAT = {value: key for key, value in REPEAT_TO_RULE.items()}
TIME_PLACEHOLDERS = {
    "hour": "Hour",
    "minute": "Min",
    "meridiem": "AM/PM",
}

THEME = {
    "window_bg": "#ece7ff",
    "shell_bg": "#f6f3ff",
    "panel_bg": "#ffffff",
    "panel_alt": "#faf7ff",
    "sidebar_bg": "#f1ebff",
    "sidebar_active": "#e7dcff",
    "primary": "#8d71f2",
    "primary_dark": "#6f57dd",
    "primary_light": "#b9a7ff",
    "accent_pink": "#8d71f2",
    "accent_rose": "#efe3ff",
    "sparkle": "#cbb6ff",
    "text": "#3f3764",
    "muted": "#7d749f",
    "line": "#e9e1ff",
    "shadow": "#ddd4fb",
    "success": "#7cbf8e",
    "warning": "#ff91ab",
}

THEME_PRESETS = {
    "purple": {
        "window_bg": "#ece7ff",
        "shell_bg": "#f6f3ff",
        "panel_bg": "#ffffff",
        "panel_alt": "#faf7ff",
        "sidebar_bg": "#f1ebff",
        "sidebar_active": "#e7dcff",
        "primary": "#8d71f2",
        "primary_dark": "#6f57dd",
        "primary_light": "#b9a7ff",
        "accent_pink": "#8d71f2",
        "accent_rose": "#efe3ff",
        "sparkle": "#cbb6ff",
        "text": "#3f3764",
        "muted": "#7d749f",
        "line": "#e9e1ff",
        "shadow": "#ddd4fb",
        "success": "#7cbf8e",
        "warning": "#8d71f2",
    },
    "blue": {
        "window_bg": "#e9f4ff",
        "shell_bg": "#f5faff",
        "panel_bg": "#ffffff",
        "panel_alt": "#f8fbff",
        "sidebar_bg": "#ebf4ff",
        "sidebar_active": "#dcecff",
        "primary": "#5b8def",
        "primary_dark": "#406fdb",
        "primary_light": "#9bc0ff",
        "accent_pink": "#73b9ff",
        "accent_rose": "#dfeeff",
        "sparkle": "#a7d7ff",
        "text": "#334466",
        "muted": "#6f819f",
        "line": "#d9e6ff",
        "shadow": "#cfe0fb",
        "success": "#6fbf9a",
        "warning": "#76a9ff",
    },
    "green": {
        "window_bg": "#e9f7ef",
        "shell_bg": "#f5fbf7",
        "panel_bg": "#ffffff",
        "panel_alt": "#f8fcf9",
        "sidebar_bg": "#eaf7ee",
        "sidebar_active": "#d9f0df",
        "primary": "#56b27f",
        "primary_dark": "#3f9768",
        "primary_light": "#98d8b0",
        "accent_pink": "#7fd6a2",
        "accent_rose": "#dff5e8",
        "sparkle": "#b8e9cb",
        "text": "#355244",
        "muted": "#6a8677",
        "line": "#d6ecd8",
        "shadow": "#c6e7cf",
        "success": "#56b27f",
        "warning": "#8fcf78",
    },
    "yellow": {
        "window_bg": "#fff6dd",
        "shell_bg": "#fffbef",
        "panel_bg": "#ffffff",
        "panel_alt": "#fffdf6",
        "sidebar_bg": "#fff3cf",
        "sidebar_active": "#ffe7a8",
        "primary": "#d8a93c",
        "primary_dark": "#b98725",
        "primary_light": "#efcc6f",
        "accent_pink": "#ffba66",
        "accent_rose": "#fff0cc",
        "sparkle": "#f5d98c",
        "text": "#5a4a2a",
        "muted": "#8a774f",
        "line": "#f1e1b0",
        "shadow": "#ead8a0",
        "success": "#7cbf8e",
        "warning": "#e0b143",
    },
    "pink": {
        "window_bg": "#ffeaf3",
        "shell_bg": "#fff5f8",
        "panel_bg": "#ffffff",
        "panel_alt": "#fff8fb",
        "sidebar_bg": "#ffe2ec",
        "sidebar_active": "#ffd2e0",
        "primary": "#ea6f9a",
        "primary_dark": "#d54f80",
        "primary_light": "#f6a8c1",
        "accent_pink": "#ff8fb8",
        "accent_rose": "#ffe0ea",
        "sparkle": "#ffc2d8",
        "text": "#5a3650",
        "muted": "#8c657d",
        "line": "#f1d4e0",
        "shadow": "#ecc2d0",
        "success": "#7cbf8e",
        "warning": "#ff91ab",
    },
}

def ensure_app_data_dir() -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def log_debug(message: str) -> None:
    try:
        ensure_app_data_dir()
        path = APP_DATA_DIR / "debug.log"
        ts = datetime.now().isoformat(timespec="seconds")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] {message}\n")
    except Exception:
        pass


def read_background_pid() -> int | None:
    try:
        return int(BACKGROUND_PID_FILE.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def write_background_heartbeat() -> None:
    ensure_app_data_dir()
    BACKGROUND_HEARTBEAT_FILE.write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")


def read_background_heartbeat() -> datetime | None:
    try:
        return datetime.fromisoformat(BACKGROUND_HEARTBEAT_FILE.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def background_process_is_running() -> bool:
    pid = read_background_pid()
    if pid is None:
        return False

    try:
        os.kill(pid, 0)
    except OSError:
        return False

    heartbeat = read_background_heartbeat()
    if heartbeat is None:
        return False

    age = (datetime.now() - heartbeat).total_seconds()
    return age <= BACKGROUND_STALE_SECONDS


if False:
        self.shell = tk.Frame(self.root, bg=THEME["shell_bg"])
        self.shell.pack(fill="both", expand=True, padx=12, pady=12)

        header = tk.Frame(self.shell, bg=THEME["panel_bg"], highlightthickness=1, highlightbackground=THEME["line"])
        header.pack(fill="x", pady=(0, 12))

        header_row = tk.Frame(header, bg=THEME["panel_bg"], padx=18, pady=14)
        header_row.pack(fill="x")

        left_title = tk.Frame(header_row, bg=THEME["panel_bg"])
        left_title.pack(side="left")
        tk.Label(left_title, text="✓", bg=THEME["panel_bg"], fg=THEME["primary"], font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Label(left_title, text="Daily To Do", bg=THEME["panel_bg"], fg=THEME["primary_dark"], font=("Segoe UI", 18, "bold")).pack(side="left", padx=(8, 0))
        tk.Label(left_title, text="Stay organized, get things done!", bg=THEME["panel_bg"], fg=THEME["muted"], font=("Segoe UI", 10)).pack(side="left", padx=(24, 0))
        tk.Label(left_title, text=" ✦", bg=THEME["panel_bg"], fg=THEME["sparkle"], font=("Segoe UI", 12, "bold")).pack(side="left")

        theme_bar = tk.Frame(header_row, bg=THEME["panel_bg"])
        theme_bar.pack(side="right")
        tk.Label(theme_bar, text="Change theme", bg=THEME["panel_bg"], fg=THEME["muted"], font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        for theme_name, color in (("purple", "#c5b0ff"), ("blue", "#9bc0ff"), ("green", "#a8dfbf"), ("yellow", "#f2d77b"), ("pink", "#f4a7c1")):
            button = tk.Button(
                theme_bar,
                text=" ",
                command=lambda name=theme_name: self.set_theme(name),
                bg=color,
                activebackground=color,
                bd=0,
                relief="flat",
                width=2,
                height=1,
                highlightthickness=1,
                highlightbackground=THEME["primary_dark"] if theme_name == self.theme_name else THEME["line"],
                cursor="hand2",
            )
            button.pack(side="left", padx=4)
            self.theme_buttons[theme_name] = button

        body = tk.Frame(self.shell, bg=THEME["shell_bg"])
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=THEME["sidebar_bg"], width=250, highlightthickness=1, highlightbackground=THEME["line"])
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)

        # sidebar Add Task button removed (Add is available in the form)

        nav_items = [("Today", "📅"), ("Upcoming", "🕒"), ("Completed", "✓"), ("All Tasks", "☰")]
        for label, icon in nav_items:
            button = tk.Button(
                sidebar,
                text=f"{icon}   {label}",
                command=lambda view=label: self.set_view(view),
                anchor="w",
                justify="left",
                bg=THEME["sidebar_active"] if label == self.active_view.get() else THEME["sidebar_bg"],
                fg=THEME["primary_dark"],
                activebackground=THEME["sidebar_active"],
                activeforeground=THEME["primary_dark"],
                bd=0,
                relief="flat",
                font=("Segoe UI", 11),
                padx=16,
                pady=10,
            )
            button.pack(fill="x", padx=14, pady=4)
            self.nav_buttons[label] = button

        mascot = tk.Frame(sidebar, bg=THEME["sidebar_bg"])
        mascot.pack(fill="both", expand=True, padx=16, pady=(18, 10))
        tk.Label(mascot, text="🐱", bg=THEME["sidebar_bg"], font=("Segoe UI Emoji", 34)).pack(pady=(12, 8))
        tk.Label(mascot, text="'Little by little,\na little becomes a lot.'", bg=THEME["sidebar_bg"], fg=THEME["muted"], justify="center", font=("Segoe UI", 10, "italic")).pack()
        tk.Label(mascot, text="♥", bg=THEME["sidebar_bg"], fg=THEME["primary_light"], font=("Segoe UI", 14, "bold")).pack(anchor="e", pady=(8, 0))

        content = tk.Frame(body, bg=THEME["shell_bg"])
        content.pack(side="left", fill="both", expand=True)

        top_wrapper, top_body = self.make_card(content)
        top_wrapper.pack(fill="x", pady=(2, 12))
        top_body.configure(padx=22, pady=18)

        title_row = tk.Frame(top_body, bg=THEME["panel_bg"])
        title_row.pack(fill="x")
        tk.Label(title_row, text="Add a new task", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(title_row, text="♥", bg=THEME["panel_bg"], fg=THEME["accent_pink"], font=("Segoe UI", 18, "bold")).pack(side="right")

        form = tk.Frame(top_body, bg=THEME["panel_bg"])
        form.pack(fill="x", pady=(16, 0))

        top_row = tk.Frame(form, bg=THEME["panel_bg"])
        top_row.pack(fill="x")

        self.task_entry = tk.Entry(
            top_row,
            textvariable=self.task_title_var,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=THEME["line"],
            highlightcolor=THEME["primary_light"],
            font=("Segoe UI", 11),
            fg=THEME["text"],
            insertbackground=THEME["text"],
            bg="white",
        )
        self.task_entry.pack(side="left", fill="x", expand=True, ipady=9, padx=(0, 10))
        self.task_entry.bind("<Return>", lambda _event: self.add_task())

        tk.Button(
            top_row,
            text="+ Add Task",
            command=self.add_task,
            bg=THEME["primary"],
            fg="white",
            activebackground=THEME["primary_dark"],
            activeforeground="white",
            bd=0,
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=16,
            pady=8,
        ).pack(side="left")

        bottom_row = tk.Frame(form, bg=THEME["panel_bg"])
        bottom_row.pack(fill="x", pady=(12, 0))

        date_box = tk.Frame(bottom_row, bg=THEME["panel_bg"])
        date_box.pack(side="left", padx=(0, 10))
        tk.Label(date_box, text="Date", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10)).pack(anchor="w")
        self.task_date_button = tk.Button(
            date_box,
            textvariable=self.task_date_display_var,
            command=self.open_task_date_picker,
            bg=THEME["panel_alt"],
            fg=THEME["text"],
            activebackground=THEME["sidebar_active"],
            activeforeground=THEME["text"],
            bd=0,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=7,
            anchor="w",
        )
        self.task_date_button.pack(anchor="w", pady=(2, 0))

        time_box = tk.Frame(bottom_row, bg=THEME["panel_bg"])
        time_box.pack(side="left", padx=(0, 10))
        tk.Label(time_box, text="Time (optional)", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10)).pack(anchor="w")
        time_row = tk.Frame(time_box, bg=THEME["panel_bg"])
        time_row.pack(anchor="w", pady=(2, 0))
        self.task_hour_combo = ttk.Combobox(time_row, textvariable=self.task_hour_var, values=[str(hour) for hour in range(1, 13)], state="readonly", width=4, justify="center", style="Modern.TCombobox")
        self.task_hour_combo.pack(side="left")
        tk.Label(time_row, text=":", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 11)).pack(side="left", padx=4)
        self.task_minute_combo = ttk.Combobox(time_row, textvariable=self.task_minute_var, values=[f"{minute:02d}" for minute in range(60)], state="readonly", width=4, justify="center", style="Modern.TCombobox")
        self.task_minute_combo.pack(side="left")
        self.task_meridiem_combo = ttk.Combobox(time_row, textvariable=self.task_meridiem_var, values=["AM", "PM"], state="readonly", width=5, justify="center", style="Modern.TCombobox")
        self.task_meridiem_combo.pack(side="left", padx=(8, 0))

        repeat_box = tk.Frame(bottom_row, bg=THEME["panel_bg"])
        repeat_box.pack(side="left", padx=(0, 10))
        tk.Label(repeat_box, text="Repeat", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10)).pack(anchor="w")
        self.task_repeat_combo = ttk.Combobox(repeat_box, textvariable=self.repeat_var, values=REPEAT_OPTIONS, state="readonly", width=12, style="Modern.TCombobox")
        self.task_repeat_combo.pack(anchor="w", pady=(2, 0))

        list_wrap = tk.Frame(content, bg=THEME["shell_bg"])
        list_wrap.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(list_wrap, bg=THEME["shell_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_wrap, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner_frame = tk.Frame(self.canvas, bg=THEME["shell_bg"])
        self.inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.update_canvas_width)
        self.canvas.bind("<Enter>", lambda _event: self.enable_mousewheel())
        self.canvas.bind("<Leave>", lambda _event: self.disable_mousewheel())

        self.saved_section, self.saved_section_body = self.make_section(self.inner_frame)
        self.completed_section, self.completed_section_body = self.make_section(self.inner_frame)

        footer = tk.Frame(content, bg=THEME["shell_bg"])
        footer.pack(fill="x", pady=(10, 0))
        tk.Label(
            footer,
            text="Press Exit App to close the app fully. You will not get reminders after exiting.",
            bg=THEME["shell_bg"],
            fg=THEME["muted"],
            font=("Segoe UI", 10),
            wraplength=720,
            justify="left",
        ).pack(side="left", fill="x", expand=True)
        tk.Button(footer, text="Exit App", command=self.exit_app, bg="#ffffff", fg=THEME["text"], bd=0, relief="flat", font=("Segoe UI", 10, "bold"), padx=14, pady=8).pack(side="right")


def restore_existing_window() -> bool:
    if os.name != "nt":
        return False

    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, WINDOW_TITLE)
        if not hwnd:
            return False

        user32.ShowWindow(hwnd, 9)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def resolve_asset_path(*parts: str) -> Path:
    candidates = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(Path(getattr(sys, "_MEIPASS")) / Path(*parts))
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / Path(*parts))
        candidates.append(exe_dir.parent / Path(*parts))
    candidates.append(Path(__file__).resolve().parent / Path(*parts))
    candidates.append(Path.cwd() / Path(*parts))
    candidates.append(APP_DATA_DIR / Path(*parts))

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


ICON_PNG_NAME = "5.png"
ICON_ICO_NAME = "5.ico"
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)


def ensure_app_icon_file() -> Path | None:
    ico_source = resolve_asset_path("assets", "images", ICON_ICO_NAME)
    if ico_source.exists():
        return ico_source

    png_path = resolve_asset_path("assets", "images", ICON_PNG_NAME)
    if not png_path.exists():
        return None

    ico_path = APP_DATA_DIR / "app.ico"
    if Image is None:
        return None

    try:
        source = Image.open(png_path).convert("RGBA")
        if max(source.size) > 256:
            source = source.resize((256, 256), Image.Resampling.LANCZOS)

        icon_frames = []
        for size in ICON_SIZES:
            frame = source.resize((size, size), Image.Resampling.LANCZOS)
            if ImageFilter is not None:
                sharpen_amount = 360 if size <= 48 else 240
                radius = 0.7 if size <= 48 else 0.9
                frame = frame.filter(
                    ImageFilter.UnsharpMask(radius=radius, percent=sharpen_amount, threshold=0)
                )
            icon_frames.append(frame)

        if not icon_frames:
            return None
        source.save(
            ico_path,
            format="ICO",
            sizes=[(size, size) for size in ICON_SIZES],
            append_images=icon_frames[1:],
        )
        return ico_path
    except Exception as exc:
        log_debug(f"ensure_app_icon_file failed: {exc}")
        return png_path if png_path.exists() else None


def load_window_icon_images() -> list[tk.PhotoImage]:
    icon_source = resolve_asset_path("assets", "images", ICON_ICO_NAME)
    if not icon_source.exists():
        icon_source = resolve_asset_path("assets", "images", ICON_PNG_NAME)
    if not icon_source.exists():
        return []

    images: list[tk.PhotoImage] = []
    try:
        if Image is not None and ImageTk is not None:
            source = Image.open(icon_source)
            if icon_source.suffix.lower() == ".ico":
                available_sizes = sorted(source.info.get("sizes", set()))
                for size in available_sizes or [(256, 256)]:
                    if hasattr(source, "ico") and source.ico is not None:
                        frame = source.ico.getimage(size).convert("RGBA")
                    else:
                        frame = source.copy().convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                    images.append(ImageTk.PhotoImage(frame))
            else:
                rgba_source = source.convert("RGBA")
                for size in (16, 32, 48, 256):
                    resized = rgba_source.resize((size, size), Image.Resampling.LANCZOS)
                    images.append(ImageTk.PhotoImage(resized))
        else:
            images.append(tk.PhotoImage(file=str(icon_source)))
    except Exception as exc:
        log_debug(f"load_window_icon_images failed: {exc}")
    return images


def apply_window_icons(root: tk.Misc, holder: object | None = None) -> None:
    images = load_window_icon_images()
    if images:
        target = holder if holder is not None else root
        setattr(target, "window_icons", images)
        try:
            root.iconphoto(True, *images)
        except Exception as exc:
            log_debug(f"iconphoto failed: {exc}")
    if os.name == "nt":
        ico_path = ensure_app_icon_file()
        if ico_path and ico_path.suffix.lower() == ".ico":
            try:
                root.iconbitmap(default=str(ico_path))
            except Exception as exc:
                log_debug(f"iconbitmap failed: {exc}")


class ThemedDialog:
    @staticmethod
    def show(parent: tk.Misc, title: str, message: str, kind: str = "info") -> None:
        ThemedDialog._open(parent, title, message, kind, buttons=("OK",))

    @staticmethod
    def ask_yes_no(parent: tk.Misc, title: str, message: str) -> bool:
        return ThemedDialog._open(parent, title, message, "confirm", buttons=("Yes", "No")) == "Yes"

    @staticmethod
    def _open(parent: tk.Misc, title: str, message: str, kind: str, buttons: tuple[str, ...]) -> str | None:
        result: dict[str, str | None] = {"value": None}
        window = tk.Toplevel(parent)
        window.title(title)
        window.resizable(False, False)
        window.configure(bg=THEME["panel_bg"])
        window.attributes("-topmost", True)
        window.transient(parent.winfo_toplevel())
        window.grab_set()
        apply_window_icons(window, window)

        wrapper = tk.Frame(window, bg=THEME["panel_bg"], padx=22, pady=18, highlightthickness=1, highlightbackground=THEME["line"])
        wrapper.pack(fill="both", expand=True)

        accent = THEME["warning"] if kind == "warning" else THEME["primary"]
        header = tk.Frame(wrapper, bg=THEME["sidebar_active"])
        header.pack(fill="x", pady=(0, 14))
        tk.Label(header, text=title, bg=THEME["sidebar_active"], fg=THEME["text"], font=("Segoe UI", 12, "bold"), padx=14, pady=10).pack(anchor="w")

        tk.Label(wrapper, text=message, bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10), justify="left", wraplength=360).pack(anchor="w")

        button_row = tk.Frame(wrapper, bg=THEME["panel_bg"])
        button_row.pack(fill="x", pady=(16, 0))
        # center the buttons and give them breathing room
        center_frame = tk.Frame(button_row, bg=THEME["panel_bg"])
        center_frame.pack()

        def choose(value: str) -> None:
            result["value"] = value
            window.destroy()

        for index, label in enumerate(reversed(buttons)):
            primary = label.lower() in {"yes", "ok"}
            tk.Button(
                center_frame,
                text=label,
                command=lambda value=label: choose(value),
                bg=accent if primary else THEME["panel_alt"],
                fg="white" if primary else THEME["text"],
                activebackground=THEME["primary_dark"] if primary else THEME["sidebar_active"],
                activeforeground="white" if primary else THEME["text"],
                bd=0,
                relief="flat",
                font=("Segoe UI", 10, "bold"),
                padx=18,
                pady=8,
            ).pack(side="left", padx=(12 if index else 0, 0))

        window.update_idletasks()
        px = parent.winfo_rootx() + max(0, (parent.winfo_width() - window.winfo_width()) // 2)
        py = parent.winfo_rooty() + max(0, (parent.winfo_height() - window.winfo_height()) // 2)
        window.geometry(f"+{px}+{py}")
        window.wait_window()
        return result["value"]


class ThemedPicker(tk.Frame):
    def __init__(self, parent: tk.Widget, variable: tk.StringVar, values: list[str], width: int = 10) -> None:
        super().__init__(parent, bg=THEME["panel_bg"])
        self.variable = variable
        self.values = values
        self.width = width
        self.popup: tk.Toplevel | None = None
        self._outside_click_bound = False
        # show a small down-arrow and render as a white outlined box so it's clearly a picker
        self.display_var = tk.StringVar(self, value=(self.variable.get() + " ▾"))
        def _sync(*_args: object) -> None:
            self.display_var.set(self.variable.get() + " ▾")

        try:
            self.variable.trace_add("write", _sync)
        except Exception:
            try:
                self.variable.trace("w", _sync)
            except Exception:
                pass

        self.button = tk.Button(
            self,
            textvariable=self.display_var,
            command=self.show_menu,
            bg="white",
            fg=THEME["text"],
            activebackground=THEME["sidebar_active"],
            activeforeground=THEME["text"],
            bd=1,
            relief="solid",
            font=("Segoe UI", 10, "bold"),
            padx=6,
            pady=5,
            anchor="w",
            width=width,
            cursor="hand2",
            highlightthickness=0,
        )
        self.button.pack(fill="both", expand=True)

    def show_menu(self) -> None:
        if self.popup is not None and self.popup.winfo_exists():
            self.close_menu()
            return

        popup = tk.Toplevel(self.button)
        self.popup = popup
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=THEME["line"])

        shell = tk.Frame(popup, bg="white", bd=1, relief="solid", highlightthickness=1, highlightbackground=THEME["line"])
        shell.pack(fill="both", expand=True)

        list_frame = tk.Frame(shell, bg="white")
        list_frame.pack(fill="both", expand=True, padx=1, pady=1)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", style="Modern.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(
            list_frame,
            bg="white",
            fg=THEME["text"],
            activestyle="none",
            selectbackground=THEME["sidebar_active"],
            selectforeground=THEME["primary_dark"],
            highlightthickness=0,
            bd=0,
            relief="flat",
            font=("Segoe UI", 10),
            exportselection=False,
            yscrollcommand=scrollbar.set,
            height=min(10, max(1, len(self.values))),
            width=max(self.width + 1, max((len(value) for value in self.values), default=6)),
        )
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        for value in self.values:
            listbox.insert("end", value)

        try:
            current_index = self.values.index(self.variable.get())
        except ValueError:
            current_index = 0
        if self.values:
            listbox.selection_set(current_index)
            listbox.activate(current_index)
            listbox.see(current_index)

        def close_popup(_event: object | None = None) -> None:
            self.close_menu()

        def choose(index: int) -> None:
            if 0 <= index < len(self.values):
                self.variable.set(self.values[index])
            close_popup()

        def on_select(_event: tk.Event | None = None) -> None:
            selection = listbox.curselection()
            if selection:
                choose(selection[0])

        def close_if_outside(event: tk.Event) -> None:
            if self.popup is None or not self.popup.winfo_exists():
                return
            widget = event.widget
            if widget is self.button:
                close_popup()
                return
            try:
                if widget.winfo_toplevel() is self.popup:
                    return
            except Exception:
                pass
            close_popup()

        listbox.bind("<ButtonRelease-1>", on_select)
        listbox.bind("<Return>", on_select)
        listbox.bind("<Escape>", close_popup)
        popup.bind("<Destroy>", lambda _event: self._unregister_outside_click())
        self._register_outside_click(close_if_outside)

        popup.update_idletasks()
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height()
        popup.geometry(f"+{x}+{y}")
        listbox.focus_set()

    def close_menu(self) -> None:
        if self.popup is not None and self.popup.winfo_exists():
            self._unregister_outside_click()
            try:
                self.popup.destroy()
            except Exception:
                pass
        self.popup = None

    def _register_outside_click(self, handler: Callable[[tk.Event], None]) -> None:
        if self._outside_click_bound:
            return
        self.winfo_toplevel().bind_all("<Button-1>", handler, add="+")
        self._outside_click_bound = True

    def _unregister_outside_click(self) -> None:
        if not self._outside_click_bound:
            return
        try:
            self.winfo_toplevel().unbind_all("<Button-1>")
        except Exception:
            pass
        self._outside_click_bound = False


def start_background_worker() -> None:
    ensure_app_data_dir()
    if background_process_is_running():
        return

    creationflags = 0
    startupinfo = None
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    if getattr(sys, "frozen", False):
        command = [sys.executable, BACKGROUND_FLAG]
    else:
        command = [sys.executable, str(Path(__file__).resolve()), BACKGROUND_FLAG]

    subprocess.Popen(
        command,
        cwd=str(APP_DATA_DIR.parent),
        creationflags=creationflags,
        startupinfo=startupinfo,
        close_fds=True,
    )
    log_debug(f"start_background_worker: spawned {' '.join(command)}")


def stop_background_worker() -> None:
    pid = read_background_pid()
    if pid is None:
        return

    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False, capture_output=True)
        else:
            os.kill(pid, 15)
    finally:
        try:
            BACKGROUND_PID_FILE.unlink()
        except FileNotFoundError:
            pass


def display_to_time(hour_text: str, minute_text: str, meridiem: str) -> str:
    hour = int(hour_text)
    minute = int(minute_text)
    if hour < 1 or hour > 12:
        raise ValueError("hour out of range")
    if minute < 0 or minute > 59:
        raise ValueError("minute out of range")
    normalized = hour % 12
    if meridiem.upper() == "PM":
        normalized += 12
    return f"{normalized:02d}:{minute:02d}"


def format_time_for_display(value: str) -> str:
    return datetime.strptime(value, "%H:%M").strftime("%I:%M %p").lstrip("0")


def add_months(source: date, months: int) -> date:
    month_index = source.month - 1 + months
    year = source.year + month_index // 12
    month = month_index % 12 + 1
    day = min(source.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def advance_due_date(current_due_date: date, repeat_rule: str) -> date:
    if repeat_rule == "weekly":
        return current_due_date + timedelta(days=7)
    if repeat_rule == "monthly":
        return add_months(current_due_date, 1)
    if repeat_rule == "annually":
        return add_months(current_due_date, 12)
    if repeat_rule == "once":
        return current_due_date
    return current_due_date + timedelta(days=1)


def first_due_date(selected_date: date, reminder_time: str, repeat_rule: str, all_day: bool) -> date:
    if all_day:
        return selected_date

    now = datetime.now()
    selected_due = datetime.combine(selected_date, datetime.strptime(reminder_time, TIME_FORMAT).time())
    if selected_due >= now:
        return selected_date

    if repeat_rule == "weekly":
        return selected_date + timedelta(days=7)
    if repeat_rule == "monthly":
        return add_months(selected_date, 1)
    if repeat_rule == "annually":
        return add_months(selected_date, 12)
    if repeat_rule == "once":
        return selected_date
    return selected_date + timedelta(days=1)


class TaskStore:
    def __init__(self, path: Path) -> None:
        ensure_app_data_dir()
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.initialize_database()

    def initialize_database(self) -> None:
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    reminder_time TEXT NOT NULL,
                    all_day INTEGER NOT NULL DEFAULT 0,
                    repeat_rule TEXT,
                    next_due_date TEXT,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    completed_today INTEGER NOT NULL DEFAULT 0,
                    reminded_today INTEGER NOT NULL DEFAULT 0,
                    last_reminded_date TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

            columns = {row["name"] for row in self.connection.execute("PRAGMA table_info(tasks)")}
            if "repeat_rule" not in columns:
                self.connection.execute("ALTER TABLE tasks ADD COLUMN repeat_rule TEXT")
            if "all_day" not in columns:
                self.connection.execute("ALTER TABLE tasks ADD COLUMN all_day INTEGER NOT NULL DEFAULT 0")
            if "next_due_date" not in columns:
                self.connection.execute("ALTER TABLE tasks ADD COLUMN next_due_date TEXT")
            if "sort_order" not in columns:
                self.connection.execute("ALTER TABLE tasks ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
            if "last_reminded_date" not in columns:
                self.connection.execute("ALTER TABLE tasks ADD COLUMN last_reminded_date TEXT")

            self.connection.execute(
                "UPDATE tasks SET repeat_rule = COALESCE(NULLIF(repeat_rule, ''), 'daily')"
            )
            self.connection.execute(
                """
                UPDATE tasks
                SET next_due_date = COALESCE(NULLIF(next_due_date, ''), date('now'))
                """
            )

            ordered_task_ids = [row["id"] for row in self.connection.execute("SELECT id FROM tasks ORDER BY created_at, id").fetchall()]
            for index, task_id in enumerate(ordered_task_ids):
                self.connection.execute("UPDATE tasks SET sort_order = ? WHERE id = ?", (index, task_id))

        # If user has an older local DB (e.g. when running from source or older builds)
        # migrate tasks into the new per-user DB so reminders continue to work.
        local_db = Path.cwd() / "todo_app.db"
        try:
            cur = self.connection.execute("SELECT COUNT(1) as c FROM tasks")
            found = cur.fetchone()[0]
        except Exception:
            found = 0

        if found == 0 and local_db.exists():
            try:
                log_debug(f"migrate: found legacy DB at {local_db}; importing tasks")
                src = sqlite3.connect(local_db)
                src.row_factory = sqlite3.Row
                rows = src.execute("SELECT id, title, reminder_time, start_date, completed_today, reminded_today, created_at FROM tasks").fetchall()
                for r in rows:
                    title = r["title"]
                    reminder_time = r["reminder_time"]
                    # map old start_date -> next_due_date
                    next_due = r["start_date"] or date.today().isoformat()
                    repeat_rule = "daily"
                    created_at = r["created_at"] or datetime.now().isoformat(timespec="seconds")
                    completed = int(r["completed_today"]) if r["completed_today"] is not None else 0
                    reminded = int(r["reminded_today"]) if r["reminded_today"] is not None else 0
                    self.connection.execute(
                        """
                        INSERT INTO tasks (title, reminder_time, all_day, repeat_rule, next_due_date, completed_today, reminded_today, last_reminded_date, created_at)
                        VALUES (?, ?, 0, ?, ?, ?, ?, NULL, ?)
                        """,
                        (title, reminder_time, repeat_rule, next_due, completed, reminded, created_at),
                    )
                src.close()
                log_debug(f"migrate: imported {len(rows)} tasks")
            except Exception as e:
                log_debug(f"migrate: failed: {e}")

    def close(self) -> None:
        self.connection.close()

    def get_setting(self, key: str) -> str | None:
        row = self.connection.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
        ).fetchone()
        return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def sync_task_states(self, today: str) -> None:
        today_date = date.fromisoformat(today)
        rows = self.connection.execute(
            """
            SELECT id, repeat_rule, next_due_date, completed_today
            FROM tasks
            """
        ).fetchall()

        for row in rows:
            if not row["completed_today"]:
                continue
            repeat_rule = row["repeat_rule"] or "daily"
            if repeat_rule == "once":
                continue

            due = date.fromisoformat(row["next_due_date"] or today)
            if due >= today_date:
                continue

            new_due = due
            while new_due < today_date:
                new_due = advance_due_date(new_due, repeat_rule)

            with self.connection:
                self.connection.execute(
                    """
                    UPDATE tasks
                    SET completed_today = 0,
                        reminded_today = 0,
                        next_due_date = ?
                    WHERE id = ?
                    """,
                    (new_due.isoformat(), row["id"]),
                )

    def add_task(self, title: str, reminder_time: str, repeat_rule: str, selected_date: date, all_day: bool) -> None:
        created_at = datetime.now().isoformat(timespec="seconds")
        due_date = first_due_date(selected_date, reminder_time, repeat_rule, all_day)
        next_sort_order = self.connection.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_sort_order FROM tasks").fetchone()["next_sort_order"]

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO tasks (
                    title,
                    reminder_time,
                    all_day,
                    repeat_rule,
                    next_due_date,
                    sort_order,
                    completed_today,
                    reminded_today,
                    last_reminded_date,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, NULL, ?)
                """,
                (
                    title.strip(),
                    reminder_time,
                    int(all_day),
                    repeat_rule,
                    due_date.isoformat(),
                    next_sort_order,
                    created_at,
                ),
            )

    def update_task(self, task_id: int, title: str, reminder_time: str, repeat_rule: str, selected_date: date, all_day: bool) -> None:
        due_date = first_due_date(selected_date, reminder_time, repeat_rule, all_day)
        with self.connection:
            self.connection.execute(
                """
                UPDATE tasks
                SET title = ?,
                    reminder_time = ?,
                    all_day = ?,
                    repeat_rule = ?,
                    next_due_date = ?
                WHERE id = ?
                """,
                (title.strip(), reminder_time, int(all_day), repeat_rule, due_date.isoformat(), task_id),
            )

    def delete_tasks_by_completion(self, completed: bool) -> int:
        with self.connection:
            cursor = self.connection.execute("DELETE FROM tasks WHERE completed_today = ?", (1 if completed else 0,))
        return cursor.rowcount if cursor.rowcount is not None else 0

    def list_tasks(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT
                id,
                title,
                reminder_time,
                all_day,
                repeat_rule,
                next_due_date,
                sort_order,
                completed_today,
                reminded_today,
                last_reminded_date,
                created_at
            FROM tasks
            ORDER BY completed_today ASC, sort_order ASC, id ASC
            """
        ).fetchall()

    def task_by_id(self, task_id: int) -> sqlite3.Row | None:
        return self.connection.execute(
            """
            SELECT id, title, reminder_time, all_day, repeat_rule, next_due_date, sort_order, completed_today
            FROM tasks
            WHERE id = ?
            """,
            (task_id,),
        ).fetchone()

    def reorder_tasks(self, task_ids: list[int]) -> None:
        if not task_ids:
            return

        subset = set(task_ids)
        ordered_subset = [task_id for task_id in task_ids if task_id in subset]
        current_order = [
            row["id"]
            for row in self.connection.execute(
                "SELECT id FROM tasks ORDER BY completed_today ASC, sort_order ASC, id ASC"
            ).fetchall()
        ]

        reordered: list[int] = []
        subset_index = 0
        for current_id in current_order:
            if current_id in subset and subset_index < len(ordered_subset):
                reordered.append(ordered_subset[subset_index])
                subset_index += 1
            else:
                reordered.append(current_id)

        with self.connection:
            for index, task_id in enumerate(reordered):
                self.connection.execute("UPDATE tasks SET sort_order = ? WHERE id = ?", (index, task_id))

    def set_completed(self, task_id: int, completed: bool) -> None:
        task = self.task_by_id(task_id)
        if task is None:
            return

        today = date.today().isoformat()
        if completed:
            with self.connection:
                self.connection.execute(
                    """
                    UPDATE tasks
                    SET completed_today = 1,
                        reminded_today = 1,
                        last_reminded_date = ?
                    WHERE id = ?
                    """,
                    (today, task_id),
                )
            return

        with self.connection:
            self.connection.execute(
                """
                UPDATE tasks
                SET completed_today = 0,
                    reminded_today = 0
                WHERE id = ?
                """,
                (task_id,),
            )

    def delete_task(self, task_id: int) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def due_tasks(self, today: str, current_time: str) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
                        SELECT id, title, reminder_time, all_day
            FROM tasks
            WHERE completed_today = 0
              AND next_due_date <= ?
                            AND all_day = 0
                            AND COALESCE(reminder_time, '') <> ''
                            AND reminder_time <= ?
              AND COALESCE(last_reminded_date, '') <> ?
            ORDER BY next_due_date, reminder_time, id
            """,
            (today, current_time, today),
        ).fetchall()

    def mark_reminded(self, task_ids: list[int]) -> None:
        if not task_ids:
            return

        placeholders = ",".join("?" for _ in task_ids)
        today = date.today().isoformat()
        with self.connection:
            self.connection.execute(
                f"""
                UPDATE tasks
                SET reminded_today = 1,
                    last_reminded_date = ?
                WHERE id IN ({placeholders})
                """,
                [today, *task_ids],
            )


class CalendarPickerPopup:
    def __init__(self, parent: tk.Widget, initial_date: date, on_pick: Callable[[date], None]) -> None:
        self.on_pick = on_pick
        self.current_year = initial_date.year
        self.current_month = initial_date.month
        self.selected_date = initial_date

        self.window = tk.Toplevel(parent)
        self.window.title("Select Date")
        self.window.resizable(False, False)
        self.window.configure(bg=THEME["panel_bg"])
        self.window.attributes("-topmost", True)
        self.window.transient(parent.winfo_toplevel())
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        apply_window_icons(self.window)

        wrapper = tk.Frame(self.window, bg=THEME["panel_bg"], padx=14, pady=14)
        wrapper.pack(fill="both", expand=True)

        header = tk.Frame(wrapper, bg=THEME["panel_bg"])
        header.pack(fill="x")
        tk.Button(header, text="◀", command=lambda: self.shift_month(-1), bg=THEME["panel_alt"], fg=THEME["text"], bd=0, relief="flat", padx=10, pady=4).pack(side="left")
        self.month_label = tk.Label(header, bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 11, "bold"))
        self.month_label.pack(side="left", expand=True)
        tk.Button(header, text="▶", command=lambda: self.shift_month(1), bg=THEME["panel_alt"], fg=THEME["text"], bd=0, relief="flat", padx=10, pady=4).pack(side="right")

        weekdays = tk.Frame(wrapper, bg=THEME["panel_bg"])
        weekdays.pack(fill="x", pady=(10, 4))
        for name in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            tk.Label(weekdays, text=name, bg=THEME["panel_bg"], fg=THEME["muted"], font=("Segoe UI", 9, "bold"), width=5).pack(side="left")

        self.days_frame = tk.Frame(wrapper, bg=THEME["panel_bg"])
        self.days_frame.pack(fill="both", expand=True)
        self.render_month()

        self.window.update_idletasks()
        x = parent.winfo_rootx() + 30
        y = parent.winfo_rooty() + 30
        self.window.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.window.lift()
        self.window.focus_force()

    def close(self) -> None:
        if hasattr(self, "window"):
            self.window.grab_release()
            self.window.destroy()

    def shift_month(self, delta: int) -> None:
        month_index = self.current_month - 1 + delta
        self.current_year += month_index // 12
        self.current_month = month_index % 12 + 1
        self.render_month()

    def render_month(self) -> None:
        for child in self.days_frame.winfo_children():
            child.destroy()

        self.month_label.configure(text=f"{calendar.month_name[self.current_month]} {self.current_year}")
        month_grid = calendar.monthcalendar(self.current_year, self.current_month)

        for week in month_grid:
            row = tk.Frame(self.days_frame, bg=THEME["panel_bg"])
            row.pack(fill="x")
            for day in week:
                if day == 0:
                    empty_cell = tk.Frame(row, bg=THEME["panel_bg"], width=44, height=30)
                    empty_cell.pack(side="left", padx=2, pady=2)
                    empty_cell.pack_propagate(False)
                    continue

                current_date = date(self.current_year, self.current_month, day)
                is_selected = current_date == self.selected_date
                tk.Button(
                    row,
                    text=str(day),
                    command=lambda selected=current_date: self.pick_date(selected),
                    bg=THEME["primary"] if is_selected else THEME["panel_alt"],
                    fg="white" if is_selected else THEME["text"],
                    activebackground=THEME["primary_dark"] if is_selected else THEME["sidebar_active"],
                    activeforeground="white" if is_selected else THEME["text"],
                    bd=0,
                    relief="flat",
                    font=("Segoe UI", 9, "bold"),
                    width=4,
                    padx=4,
                    pady=4,
                ).pack(side="left", padx=2, pady=2)

    def pick_date(self, selected_date: date) -> None:
        self.on_pick(selected_date)
        self.close()

class ReminderDialog:
    def __init__(self, app: "TodoApp", tasks: list[sqlite3.Row]) -> None:
        self.app = app
        self.tasks = tasks

        self.window = tk.Toplevel(app.root)
        self.window.title("Reminder")
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)
        if self.app.show_ui and self.app.root.state() == "normal":
            self.window.transient(app.root)
            self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.on_ok)
        self.window.configure(bg=THEME["panel_bg"])
        apply_window_icons(self.window)

        outer = tk.Frame(self.window, bg=THEME["panel_bg"], highlightthickness=1, highlightbackground=THEME["line"])
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=THEME["sidebar_active"], height=44)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🔔", bg=THEME["sidebar_active"], fg=THEME["primary"], font=("Segoe UI", 12, "bold")).pack(side="left", padx=(12, 6), pady=8)
        tk.Label(header, text="Reminder", bg=THEME["sidebar_active"], fg=THEME["text"], font=("Segoe UI", 11, "bold")).pack(side="left", pady=8)

        container = tk.Frame(outer, bg=THEME["panel_bg"], padx=18, pady=16)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="Time to complete your task!",
            bg=THEME["panel_bg"],
            fg=THEME["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="center", pady=(0, 10))

        # reminder image (1.png) is shown above; remove the emoji/bell so only the image displays
        # try to load a reminder image `assets/images/1.png`, fall back to emoji if missing
        try:
            rem_path = resolve_asset_path("assets", "images", "1.png")
            if rem_path.exists():
                if Image is not None and ImageTk is not None:
                    pil_img = Image.open(rem_path)
                    target_w = 135
                    if pil_img.width > target_w:
                        ratio = target_w / float(pil_img.width)
                        target_h = max(1, int(pil_img.height * ratio))
                        pil_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    self.reminder_image = ImageTk.PhotoImage(pil_img)
                else:
                    self.reminder_image = tk.PhotoImage(file=str(rem_path))
                tk.Label(container, image=self.reminder_image, bg=THEME["panel_bg"]).pack(anchor="center", pady=(0, 8))
        except Exception as exc:
            log_debug(f"ReminderDialog: failed loading reminder image: {exc}")

        title_box = tk.Frame(container, bg=THEME["panel_alt"], padx=14, pady=10)
        title_box.pack(fill="x", pady=(4, 12))
        tk.Label(
            title_box,
            text="\n".join(task["title"] for task in tasks),
            bg=THEME["panel_alt"],
            fg=THEME["text"],
            justify="center",
            font=("Segoe UI", 10, "bold"),
        ).pack()

        time_badge = tk.Frame(container, bg=THEME["sidebar_active"], padx=12, pady=8)
        time_badge.pack(anchor="center", pady=(0, 14))
        tk.Label(
            time_badge,
            text=f"⏰ {self.app.task_time_label(tasks[0])}",
            bg=THEME["sidebar_active"],
            fg=THEME["primary_dark"],
            font=("Segoe UI", 11, "bold"),
        ).pack()

        button_row = tk.Frame(container, bg=THEME["panel_bg"])
        button_row.pack(fill="x")

        center_row = tk.Frame(button_row, bg=THEME["panel_bg"])
        center_row.pack(anchor="center")

        tk.Button(
            center_row,
            text="OK",
            command=self.on_ok,
            bg=THEME["primary"],
            fg="white",
            bd=0,
            activebackground=THEME["primary_dark"],
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=24,
            pady=13,
        ).pack(side="left", padx=(0, 10))
        tk.Button(
            center_row,
            text="Mark as complete",
            command=self.on_mark_completed,
            bg=THEME["accent_pink"],
            fg="white",
            bd=0,
            activebackground=THEME["primary_dark"],
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=24,
            pady=13,
        ).pack(side="left")

        self.window.update_idletasks()
        width = 360
        height = 420
        x = app.root.winfo_rootx() + app.root.winfo_width() - width - 20
        y = app.root.winfo_rooty() + app.root.winfo_height() - height - 20
        self.window.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")
        self.window.lift()
        self.window.focus_force()

    def on_ok(self) -> None:
        ids = [task["id"] for task in self.tasks]
        log_debug(f"ReminderDialog.on_ok: dismissing reminder for {ids}")
        self.app.store.mark_reminded(ids)
        self.close()

    def on_mark_completed(self) -> None:
        ids = []
        for task in self.tasks:
            tid = int(task["id"])
            ids.append(tid)
            self.app.store.set_completed(tid, True)
        log_debug(f"ReminderDialog.on_mark_completed: completed {ids}")
        self.close()

    def close(self) -> None:
        if self.app.reminder_dialog is self:
            self.app.reminder_dialog = None
        if hasattr(self, "window"):
            if self.app.show_ui and self.app.root.state() == "normal":
                self.window.grab_release()
            self.window.destroy()
        self.app.refresh_tasks()


class TodoApp:
    def __init__(self, root: tk.Tk, show_ui: bool = True, window_title: str = WINDOW_TITLE) -> None:
        self.root = root
        self.show_ui = show_ui
        self.theme_name = "purple"
        self.root.title(window_title)
        self.root.geometry("1150x760")
        self.root.minsize(940, 660)
        self.root.resizable(True, True)
        self.root.configure(bg=THEME["window_bg"])

        self.store = TaskStore(DB_PATH)
        self.reminder_dialog: ReminderDialog | None = None
        self.active_view = tk.StringVar(value="Today")

        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        self.style.configure("TFrame", background=THEME["window_bg"])
        self.style.configure("TLabel", background=THEME["window_bg"], foreground=THEME["text"], font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(10, 6))
        self.apply_widget_styles()

        self.task_title_var = tk.StringVar()
        self.window_icons: list[tk.PhotoImage] = []
        self.task_date_var = tk.StringVar(value=date.today().isoformat())
        self.task_date_display_var = tk.StringVar(value=self.format_date_for_display(date.today()))
        self.task_hour_var = tk.StringVar(value=TIME_PLACEHOLDERS["hour"])
        self.task_minute_var = tk.StringVar(value=TIME_PLACEHOLDERS["minute"])
        self.task_meridiem_var = tk.StringVar(value=TIME_PLACEHOLDERS["meridiem"])
        self.repeat_var = tk.StringVar(value="Once")
        self.status_var = tk.StringVar(value="Add a task, choose a repeat rule, and check it off when done.")

        self.base_font = tkfont.nametofont("TkDefaultFont")
        self.title_font = self.base_font.copy()
        self.completed_font = self.base_font.copy()
        self.completed_font.configure(overstrike=1)
        # make task titles slightly larger for readability
        try:
            self.title_font.configure(size=self.title_font.cget("size") + 2)
        except Exception:
            pass

        self.nav_buttons: dict[str, tk.Button] = {}
        self.theme_buttons: dict[str, tk.Button] = {}
        self.quote_image: tk.PhotoImage | None = None
        self.empty_state_images: list[tk.PhotoImage] = []
        self.dragged_task_id: int | None = None
        self.dragged_task_parent: tk.Widget | None = None
        self.dragged_row: tk.Widget | None = None

        # ensure empty-state images exist so the UI can display them
        self.ensure_empty_state_images()

        if self.show_ui:
            apply_window_icons(self.root, self)
            self.build_ui()
            self.refresh_tasks()
        # Always schedule checks so the UI can show reminders when the background worker
        # is not running (helps when background failed to start). If a background
        # worker is active, the UI will skip showing reminders to avoid duplicates.
        self.schedule_checks()
        if self.show_ui:
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def apply_widget_styles(self) -> None:
        self.style.configure("TFrame", background=THEME["window_bg"])
        self.style.configure("TLabel", background=THEME["window_bg"], foreground=THEME["text"], font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(10, 6))
        self.style.configure(
            "Modern.Vertical.TScrollbar",
            background=THEME["primary_light"],
            troughcolor=THEME["shell_bg"],
            bordercolor=THEME["line"],
            arrowcolor=THEME["primary_dark"],
            relief="flat",
            gripcount=0,
        )
        self.style.map(
            "Modern.Vertical.TScrollbar",
            background=[("active", THEME["primary"]), ("pressed", THEME["primary_dark"])],
        )

    def bind_mousewheel(self, widget: tk.Widget) -> None:
        widget.bind("<MouseWheel>", self.on_mousewheel, add="+")
        widget.bind("<Button-4>", self.on_mousewheel, add="+")
        widget.bind("<Button-5>", self.on_mousewheel, add="+")

    def bind_mousewheel_tree(self, widget: tk.Widget) -> None:
        self.bind_mousewheel(widget)
        for child in widget.winfo_children():
            self.bind_mousewheel_tree(child)

    def create_large_checkbox(self, parent: tk.Widget, variable: tk.BooleanVar, command: Callable[[], None]) -> tk.Frame:
        frame = tk.Frame(parent, bg=THEME["panel_bg"], width=34, height=34)
        frame.grid_propagate(False)
        box = tk.Label(
            frame,
            text="",
            bg="white",
            fg=THEME["primary"],
            font=("Segoe UI", 20, "bold"),
            relief="solid",
            bd=1,
            highlightthickness=2,
            highlightbackground=THEME["line"],
            highlightcolor=THEME["primary"],
            cursor="hand2",
        )
        box.place(relx=0.5, rely=0.5, anchor="center", width=28, height=28)

        def refresh(*_args: object) -> None:
            box.configure(text="✓" if variable.get() else "")

        def toggle(_event: tk.Event | None = None) -> None:
            variable.set(not variable.get())
            command()

        variable.trace_add("write", refresh)
        for target in (frame, box):
            target.bind("<Button-1>", toggle)
        refresh()
        return frame

    def build_ui(self) -> None:
        self.shell = tk.Frame(self.root, bg=THEME["shell_bg"])
        self.shell.pack(fill="both", expand=True, padx=12, pady=12)

        header = tk.Frame(self.shell, bg=THEME["panel_bg"], highlightthickness=1, highlightbackground=THEME["line"])
        header.pack(fill="x", pady=(0, 12))

        header_row = tk.Frame(header, bg=THEME["panel_bg"], padx=18, pady=14)
        header_row.pack(fill="x")

        left_title = tk.Frame(header_row, bg=THEME["panel_bg"])
        left_title.pack(side="left")
        tk.Label(left_title, text="✓", bg=THEME["panel_bg"], fg=THEME["primary"], font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Label(left_title, text="Daily To Do", bg=THEME["panel_bg"], fg=THEME["primary_dark"], font=("Segoe UI", 18, "bold")).pack(side="left", padx=(8, 0))
        tk.Label(left_title, text="Stay organized, get things done!", bg=THEME["panel_bg"], fg=THEME["muted"], font=("Segoe UI", 10)).pack(side="left", padx=(24, 0))
        # sparkle marker separated so we can style it lightly per theme
        tk.Label(left_title, text="✦", bg=THEME["panel_bg"], fg=THEME["sparkle"], font=("Segoe UI", 12, "bold")).pack(side="left")

        theme_bar = tk.Frame(header_row, bg=THEME["panel_bg"])
        theme_bar.pack(side="right")
        tk.Label(theme_bar, text="Select theme", bg=THEME["panel_bg"], fg=THEME["muted"], font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        for theme_name, color in (("purple", "#c5b0ff"), ("blue", "#9bc0ff"), ("green", "#a8dfbf"), ("yellow", "#f2d77b"), ("pink", "#f4a7c1")):
            button = tk.Button(
                theme_bar,
                text=" ",
                command=lambda name=theme_name: self.set_theme(name),
                bg=color,
                activebackground=color,
                bd=0,
                relief="flat",
                width=2,
                height=1,
                highlightthickness=1,
                highlightbackground=THEME["primary_dark"] if theme_name == self.theme_name else THEME["line"],
                cursor="hand2",
            )
            button.pack(side="left", padx=4)
            self.theme_buttons[theme_name] = button

        body = tk.Frame(self.shell, bg=THEME["shell_bg"])
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=THEME["sidebar_bg"], width=250, highlightthickness=1, highlightbackground=THEME["line"])
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)

        nav_items = [("Today", "📅"), ("Upcoming", "🕒"), ("Completed", "✓"), ("All Tasks", "☰")]
        for label, icon in nav_items:
            button = tk.Button(
                sidebar,
                text=f"{icon}   {label}",
                command=lambda view=label: self.set_view(view),
                anchor="w",
                justify="left",
                bg=THEME["sidebar_active"] if label == self.active_view.get() else THEME["sidebar_bg"],
                fg=THEME["primary_dark"],
                activebackground=THEME["sidebar_active"],
                activeforeground=THEME["primary_dark"],
                bd=0,
                relief="flat",
                font=("Segoe UI", 11),
                padx=16,
                pady=10,
            )
            button.pack(fill="x", padx=14, pady=4)
            self.nav_buttons[label] = button

        mascot = tk.Frame(sidebar, bg=THEME["sidebar_bg"])
        mascot.pack(fill="both", expand=True, padx=16, pady=(18, 10))
        image_loaded = False
        image_path = resolve_asset_path("assets", "images", "2.png")
        try:
            if image_path.exists():
                if Image is not None and ImageTk is not None:
                    pil_image = Image.open(image_path)
                    target_width = 120
                    if pil_image.width > target_width:
                        ratio = target_width / float(pil_image.width)
                        target_height = max(1, int(pil_image.height * ratio))
                        pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    image = ImageTk.PhotoImage(pil_image)
                else:
                    image = tk.PhotoImage(file=str(image_path))
                    if image.width() > 140:
                        factor = max(1, image.width() // 120)
                        image = image.subsample(factor, factor)

                self.quote_image = image
                tk.Label(mascot, image=self.quote_image, bg=THEME["sidebar_bg"]).pack(pady=(12, 8))
                image_loaded = True
        except Exception as exc:
            log_debug(f"sidebar image load failed for {image_path}: {exc}")

        if not image_loaded:
            tk.Label(mascot, text="🐱", bg=THEME["sidebar_bg"], font=("Segoe UI Emoji", 34)).pack(pady=(12, 8))
        tk.Label(mascot, text="'Little by little,\na little becomes a lot.'", bg=THEME["sidebar_bg"], fg=THEME["muted"], justify="center", font=("Segoe UI", 10, "italic")).pack()
        tk.Label(mascot, text="♥", bg=THEME["sidebar_bg"], fg=THEME["accent_pink"], font=("Segoe UI", 14, "bold")).pack(anchor="e", pady=(8, 0))

        content = tk.Frame(body, bg=THEME["shell_bg"])
        content.pack(side="left", fill="both", expand=True)

        top_wrapper, top_body = self.make_card(content)
        top_wrapper.pack(fill="x", pady=(2, 12))
        top_body.configure(padx=22, pady=18)

        title_row = tk.Frame(top_body, bg=THEME["panel_bg"])
        title_row.pack(fill="x")
        tk.Label(title_row, text="Add a new task", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(title_row, text="♥", bg=THEME["panel_bg"], fg=THEME["accent_pink"], font=("Segoe UI", 18, "bold")).pack(side="right")

        form = tk.Frame(top_body, bg=THEME["panel_bg"])
        form.pack(fill="x", pady=(16, 0))

        top_row = tk.Frame(form, bg=THEME["panel_bg"])
        top_row.pack(fill="x")

        entry_shell = tk.Frame(
            top_row,
            bg="white",
            highlightthickness=1,
            highlightbackground=THEME["line"],
            highlightcolor=THEME["primary_light"],
        )
        entry_shell.pack(side="left", fill="x", expand=True, padx=(0, 10))
        # reduced left padding to make the input area a little tighter
        tk.Label(entry_shell, text=" ", bg="white", fg=THEME["text"], font=("Segoe UI", 11), width=1).pack(side="left", padx=(6, 0), pady=6)
        self.task_entry = tk.Entry(
            entry_shell,
            textvariable=self.task_title_var,
            bd=0,
            relief="flat",
            highlightthickness=0,
            font=("Segoe UI", 11),
            fg=THEME["text"],
            insertbackground=THEME["text"],
            bg="white",
        )
        # slightly reduce vertical padding inside the box while keeping some space
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=6, ipady=1)
        self.task_entry.bind("<Return>", lambda _event: self.add_task())
        self.task_entry.bind("<KeyRelease>", lambda _event: self._capitalize_var(self.task_title_var))

        tk.Button(
            top_row,
            text="+ Add Task",
            command=self.add_task,
            bg=THEME["primary"],
            fg="white",
            activebackground=THEME["primary_dark"],
            activeforeground="white",
            bd=0,
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=16,
            pady=8,
        ).pack(side="left")

        bottom_row = tk.Frame(form, bg=THEME["panel_bg"])
        bottom_row.pack(fill="x", pady=(12, 0))

        date_box = tk.Frame(bottom_row, bg=THEME["panel_bg"])
        date_box.pack(side="left", padx=(0, 10))
        tk.Label(date_box, text="Date", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10)).pack(anchor="w")
        self.task_date_button = tk.Button(
            date_box,
            textvariable=self.task_date_display_var,
            command=self.open_task_date_picker,
            bg=THEME["panel_alt"],
            fg=THEME["text"],
            activebackground=THEME["sidebar_active"],
            activeforeground=THEME["text"],
            bd=0,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=7,
            anchor="w",
        )
        self.task_date_button.pack(anchor="w", pady=(2, 0))

        time_box = tk.Frame(bottom_row, bg=THEME["panel_bg"])
        time_box.pack(side="left", padx=(0, 8))
        tk.Label(time_box, text="Time (optional)", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10)).pack(anchor="w")
        time_row = tk.Frame(time_box, bg=THEME["panel_bg"])
        time_row.pack(anchor="w", pady=(2, 0))
        self.task_hour_picker = ThemedPicker(time_row, self.task_hour_var, [str(hour) for hour in range(1, 13)], width=5)
        self.task_hour_picker.pack(side="left")
        tk.Label(time_row, text=":", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 11)).pack(side="left", padx=4)
        self.task_minute_picker = ThemedPicker(time_row, self.task_minute_var, [f"{minute:02d}" for minute in range(60)], width=4)
        self.task_minute_picker.pack(side="left")
        self.task_meridiem_picker = ThemedPicker(time_row, self.task_meridiem_var, ["AM", "PM"], width=7)
        self.task_meridiem_picker.pack(side="left", padx=(6, 0))

        repeat_box = tk.Frame(bottom_row, bg=THEME["panel_bg"])
        repeat_box.pack(side="left", padx=(0, 6))
        tk.Label(repeat_box, text="Repeat", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10)).pack(anchor="w")
        # make repeat picker compact and clearly a dropdown
        self.task_repeat_picker = ThemedPicker(repeat_box, self.repeat_var, REPEAT_OPTIONS, width=12)
        self.task_repeat_picker.pack(anchor="w", pady=(2, 0))

        self.list_wrap = tk.Frame(content, bg=THEME["shell_bg"])
        self.list_wrap.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.list_wrap, bg=THEME["shell_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.list_wrap, orient="vertical", command=self.canvas.yview, style="Modern.Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner_frame = tk.Frame(self.canvas, bg=THEME["shell_bg"])
        self.inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.update_canvas_width)
        for widget in (self.list_wrap, self.canvas, self.inner_frame):
            self.bind_mousewheel(widget)

        self.saved_section, self.saved_section_body = self.make_section(self.inner_frame)
        self.completed_section, self.completed_section_body = self.make_section(self.inner_frame)

        footer = tk.Frame(content, bg=THEME["shell_bg"])
        footer.pack(fill="x", pady=(10, 0))
        tk.Label(
            footer,
            text="Press Exit App to close the app fully. You will not get reminders after exiting.",
            bg=THEME["shell_bg"],
            fg=THEME["muted"],
            font=("Segoe UI", 10),
            wraplength=720,
            justify="left",
        ).pack(side="left", fill="x", expand=True)
        tk.Button(footer, text="Exit App", command=self.exit_app, bg="#ffffff", fg=THEME["text"], bd=0, relief="flat", font=("Segoe UI", 10, "bold"), padx=14, pady=8).pack(side="right")

    def set_theme(self, theme_name: str) -> None:
        if theme_name not in THEME_PRESETS:
            return

        self.theme_name = theme_name
        THEME.clear()
        THEME.update(THEME_PRESETS[theme_name])

        if not self.show_ui:
            return

        self.root.configure(bg=THEME["window_bg"])
        self.apply_widget_styles()

        task_state = {
            "title": self.task_title_var.get(),
            "hour": self.task_hour_var.get(),
            "minute": self.task_minute_var.get(),
            "meridiem": self.task_meridiem_var.get(),
            "repeat": self.repeat_var.get(),
            "view": self.active_view.get(),
        }

        for child in self.root.winfo_children():
            child.destroy()

        self.nav_buttons = {}
        self.theme_buttons = {}
        self.task_title_var.set(task_state["title"])
        self.task_hour_var.set(task_state["hour"])
        self.task_minute_var.set(task_state["minute"])
        self.task_meridiem_var.set(task_state["meridiem"])
        self.repeat_var.set(task_state["repeat"])
        self.active_view.set(task_state["view"])

        self.build_ui()
        self.refresh_tasks()

    def make_card(self, parent: tk.Widget) -> tuple[tk.Frame, tk.Frame]:
        wrapper = tk.Frame(parent, bg=THEME["panel_bg"], highlightthickness=1, highlightbackground=THEME["shadow"])
        body = tk.Frame(wrapper, bg=THEME["panel_bg"])
        body.pack(fill="both", expand=True)
        return wrapper, body

    def make_section(self, parent: tk.Widget) -> tuple[tk.Frame, tk.Frame]:
        wrapper, body = self.make_card(parent)
        wrapper.pack(fill="x", pady=(0, 12))
        body.configure(padx=22, pady=18)
        return wrapper, body

    def make_badge(self, parent: tk.Widget, text: str, bg: str, fg: str) -> tk.Frame:
        badge = tk.Frame(parent, bg=bg, padx=10, pady=4)
        tk.Label(badge, text=text, bg=bg, fg=fg, font=("Segoe UI", 9)).pack()
        return badge

    def format_date_for_display(self, selected_date: date) -> str:
        return selected_date.strftime("%a, %b %d, %Y")

    def set_task_date(self, selected_date: date) -> None:
        self.task_date_var.set(selected_date.isoformat())
        self.task_date_display_var.set(self.format_date_for_display(selected_date))

    def open_task_date_picker(self) -> None:
        try:
            initial = datetime.strptime(self.task_date_var.get(), "%Y-%m-%d").date()
        except ValueError:
            initial = date.today()
        CalendarPickerPopup(self.task_date_button, initial, self.set_task_date)

    def normalize_task_title(self, value: str) -> str:
        value = value.strip()
        if not value:
            return value
        return value[:1].upper() + value[1:]

    def capitalize_task_title_text(self, value: str) -> str:
        if not value:
            return value
        first_non_space = next((index for index, char in enumerate(value) if not char.isspace()), None)
        if first_non_space is None:
            return value
        if value[first_non_space].isalpha():
            return value[:first_non_space] + value[first_non_space].upper() + value[first_non_space + 1 :]
        return value

    def normalize_time_input(self, value: str, placeholder: str) -> str:
        cleaned = value.strip()
        if not cleaned or cleaned == placeholder:
            return ""
        return cleaned

    def reset_time_fields(self) -> None:
        self.task_hour_var.set(TIME_PLACEHOLDERS["hour"])
        self.task_minute_var.set(TIME_PLACEHOLDERS["minute"])
        self.task_meridiem_var.set(TIME_PLACEHOLDERS["meridiem"])

    def capitalize_task_title(self, event: tk.Event | None = None) -> None:
        self._capitalize_var(self.task_title_var)

    def _capitalize_var(self, text_var: tk.StringVar) -> None:
        normalized = self.capitalize_task_title_text(text_var.get())
        if normalized != text_var.get():
            text_var.set(normalized)

    def open_edit_date_picker(self, date_var: tk.StringVar, display_var: tk.StringVar, anchor: tk.Widget) -> None:
        try:
            initial = datetime.strptime(date_var.get(), "%Y-%m-%d").date()
        except ValueError:
            initial = date.today()

        def set_date(selected_date: date) -> None:
            date_var.set(selected_date.isoformat())
            display_var.set(self.format_date_for_display(selected_date))

        CalendarPickerPopup(anchor, initial, set_date)

    def focus_task_entry(self) -> None:
        if hasattr(self, "task_entry"):
            self.task_entry.focus_set()

    def set_view(self, view: str) -> None:
        self.active_view.set(view)
        self.refresh_tasks()

    def view_allows_task(self, task: sqlite3.Row, view: str) -> bool:
        today = date.today().isoformat()
        due_date = task["next_due_date"] or today
        if view == "All Tasks":
            return True
        if view == "Completed":
            return True
        if view == "Upcoming":
            return due_date > today
        return due_date == today

    def view_section_labels(self, view: str) -> dict[str, str | bool]:
        if view == "Today":
            return {
                "show_saved": True,
                "saved_title": "Today's Tasks",
                "saved_subtitle": "Tasks due today that are still open.",
                "saved_empty": "No tasks due today yet.",
                "saved_image": "3.png",
                "completed_title": "Today's Completed Tasks",
                "completed_subtitle": "Tasks completed today.",
                "completed_empty": "No completed tasks today.",
                "completed_image": "4.png",
            }
        if view == "Upcoming":
            return {
                "show_saved": True,
                "saved_title": "Upcoming Tasks",
                "saved_subtitle": "Future tasks still open.",
                "saved_empty": "No upcoming tasks yet.",
                "saved_image": "3.png",
                "completed_title": "Early Completed Upcoming Tasks",
                "completed_subtitle": "Future tasks already marked complete.",
                "completed_empty": "No early completed upcoming tasks yet.",
                "completed_image": "4.png",
            }
        if view == "Completed":
            return {
                "show_saved": False,
                "completed_title": "Completed Tasks",
                "completed_subtitle": "Everything you've completed.",
                "completed_empty": "No completed tasks yet.",
                "completed_image": "4.png",
            }
        return {
            "show_saved": True,
            "saved_title": "Saved Tasks",
            "saved_subtitle": "Open tasks still pending.",
            "saved_empty": "No saved tasks yet.",
            "saved_image": "3.png",
            "completed_title": "Completed Tasks",
            "completed_subtitle": "All completed tasks.",
            "completed_empty": "No completed tasks yet.",
            "completed_image": "4.png",
        }

    def update_scroll_region(self, _event: tk.Event | None = None) -> None:
        if not self.show_ui:
            return
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_canvas_width(self, event: tk.Event) -> None:
        if not self.show_ui:
            return
        self.canvas.itemconfigure(self.inner_window, width=event.width)

    def on_mousewheel(self, event: tk.Event) -> None:
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 * int(event.delta / 120)
        self.canvas.yview_scroll(delta, "units")

    def ensure_empty_state_images(self) -> None:
        try:
            names = [("3.png", "Saved"), ("4.png", "Completed")]
            for name, label in names:
                image_path = resolve_asset_path("assets", "images", name)
                try:
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass

                if image_path.exists():
                    continue

                try:
                    if Image is not None:
                        from PIL import ImageDraw, ImageFont

                        w, h = 480, 320
                        bg = THEME.get("panel_alt", "#faf7ff")
                        img = Image.new("RGBA", (w, h), bg)
                        draw = ImageDraw.Draw(img)
                        try:
                            font = ImageFont.load_default()
                        except Exception:
                            font = None
                        text = label
                        if font is not None:
                            tw, th = draw.textsize(text, font=font)
                        else:
                            tw, th = draw.textsize(text)
                        draw.text(((w - tw) / 2, (h - th) / 2), text, fill=THEME.get("muted", "#7d749f"), font=font)
                        img.save(image_path)
                    else:
                        # fallback: write a single transparent pixel PNG
                        import base64

                        tiny_png = base64.b64decode(
                            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
                        )
                        with open(image_path, "wb") as fh:
                            fh.write(tiny_png)
                except Exception as exc:
                    log_debug(f"ensure_empty_state_images: failed creating {image_path}: {exc}")
        except Exception:
            # keep UI resilient; don't raise on startup image creation failures
            pass

    def clear_section(self, section: ttk.Frame) -> None:
        if not self.show_ui:
            return
        for child in section.winfo_children():
            child.destroy()

    def section_header(
        self,
        parent: ttk.Frame,
        title: str,
        subtitle: str,
        action_text: str | None = None,
        action_command: Callable[[], None] | None = None,
    ) -> None:
        if not self.show_ui:
            return
        header = tk.Frame(parent, bg=THEME["panel_bg"])
        header.pack(fill="x", pady=(0, 10))
        left = tk.Frame(header, bg=THEME["panel_bg"])
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=title, bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(left, text=subtitle, bg=THEME["panel_bg"], fg=THEME["muted"], font=("Segoe UI", 10)).pack(side="left", padx=(8, 0))
        if action_text and action_command:
            tk.Button(
                header,
                text=action_text,
                command=action_command,
                bg=THEME["panel_alt"],
                fg=THEME["primary_dark"],
                bd=0,
                activebackground=THEME["sidebar_active"],
                activeforeground=THEME["primary_dark"],
                relief="flat",
                font=("Segoe UI", 9, "bold"),
                padx=12,
                pady=5,
            ).pack(side="right")

    def task_time_label(self, task: sqlite3.Row) -> str:
        if int(task["all_day"] or 0) == 1:
            return "All day"
        return format_time_for_display(task["reminder_time"])

    def refresh_tasks(self) -> None:
        if not self.show_ui:
            return
        today = date.today().isoformat()
        self.store.sync_task_states(today)

        self.empty_state_images.clear()

        self.clear_section(self.saved_section_body)
        self.clear_section(self.completed_section_body)
        self.saved_section.pack_forget()
        self.completed_section.pack_forget()

        saved_tasks = []
        completed_tasks = []
        view = self.active_view.get()
        layout = self.view_section_labels(view)
        for task in self.store.list_tasks():
            if not self.view_allows_task(task, view):
                continue
            if task["completed_today"]:
                completed_tasks.append(task)
            else:
                saved_tasks.append(task)

        if layout["show_saved"]:
            self.saved_section.pack(fill="x", pady=(0, 12))
            self.section_header(
                self.saved_section_body,
                str(layout["saved_title"]),
                str(layout["saved_subtitle"]),
                "Clear All",
                lambda completed=False: self.clear_tasks(completed),
            )
            if not saved_tasks:
                self.empty_state(self.saved_section_body, str(layout["saved_empty"]), layout["saved_image"])
            else:
                for task in saved_tasks:
                    self.create_task_row(self.saved_section_body, task, checked=False)
        else:
            self.saved_section.pack_forget()

        self.completed_section.pack(fill="x", pady=(0, 12))
        self.section_header(
            self.completed_section_body,
            str(layout["completed_title"]),
            str(layout["completed_subtitle"]),
            "Clear All",
            lambda completed=True: self.clear_tasks(completed),
        )
        if not completed_tasks:
            self.empty_state(self.completed_section_body, str(layout["completed_empty"]), layout["completed_image"])
        else:
            for task in completed_tasks:
                self.create_task_row(self.completed_section_body, task, checked=True)

        self.update_scroll_region()

        for label, button in self.nav_buttons.items():
            button.configure(bg=THEME["sidebar_active"] if label == view else THEME["sidebar_bg"])

        self.bind_mousewheel_tree(self.saved_section)
        self.bind_mousewheel_tree(self.completed_section)

    def empty_state(self, parent: tk.Widget, message: str, image_name: str | None = None) -> None:
        box = tk.Frame(parent, bg=THEME["panel_bg"], pady=28)
        box.pack(fill="x")

        image_loaded = False
        if image_name:
            image_path = resolve_asset_path("assets", "images", image_name)
            try:
                if image_path.exists():
                    if Image is not None and ImageTk is not None:
                        pil_image = Image.open(image_path)
                        target_width = 150
                        if pil_image.width > target_width:
                            ratio = target_width / float(pil_image.width)
                            target_height = max(1, int(pil_image.height * ratio))
                            pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                        image = ImageTk.PhotoImage(pil_image)
                    else:
                        image = tk.PhotoImage(file=str(image_path))
                        if image.width() > 170:
                            factor = max(1, image.width() // 150)
                            image = image.subsample(factor, factor)

                    self.empty_state_images.append(image)
                    tk.Label(box, image=image, bg=THEME["panel_bg"]).pack(pady=(0, 8))
                    image_loaded = True
            except Exception as exc:
                log_debug(f"empty_state image load failed for {image_path}: {exc}")

        if not image_loaded:
            tk.Label(box, text="📋", bg=THEME["panel_bg"], fg=THEME["primary_light"], font=("Segoe UI Emoji", 28)).pack(pady=(0, 8))

        tk.Label(box, text=message, bg=THEME["panel_bg"], fg=THEME["muted"], justify="center", font=("Segoe UI", 10)).pack()

    def create_task_row(self, parent: ttk.Frame, task: sqlite3.Row, checked: bool) -> None:
        if not self.show_ui:
            return
        row = tk.Frame(parent, bg=THEME["panel_bg"], bd=1, relief="solid", highlightthickness=1, highlightbackground=THEME["line"])
        row._task_id = task["id"]  # type: ignore[attr-defined]
        row.pack(fill="x", pady=6)

        toggle_var = tk.BooleanVar(value=checked)
        checkbox = self.create_large_checkbox(
            row,
            toggle_var,
            lambda task_id=task["id"], var=toggle_var: self.on_task_toggle(task_id, var.get()),
        )
        checkbox.grid(row=0, column=0, rowspan=2, padx=14, pady=8, sticky="ns")

        title_font = self.completed_font if checked else self.title_font
        title_label = tk.Label(
            row,
            text=task["title"],
            font=title_font,
            bg=THEME["panel_bg"],
            fg=THEME["text"] if not checked else THEME["muted"],
            anchor="w",
        )
        title_label.grid(row=0, column=1, sticky="w", pady=(10, 0))

        badge_row = tk.Frame(row, bg=THEME["panel_bg"])
        badge_row.grid(row=1, column=1, sticky="w", pady=(6, 10))
        self.make_badge(badge_row, f"⏰ {self.task_time_label(task)}", THEME["accent_rose"], THEME["primary_dark"]).pack(side="left", padx=(0, 8))
        self.make_badge(badge_row, f"📅 {RULE_TO_REPEAT.get(task['repeat_rule'] or 'daily', 'Daily')}", THEME["panel_alt"], THEME["muted"]).pack(side="left", padx=(0, 8))
        self.make_badge(badge_row, self.task_status_text(task), THEME["accent_pink"] if not checked else THEME["panel_alt"], "white" if not checked else THEME["muted"]).pack(side="left")

        actions = tk.Frame(row, bg=THEME["panel_bg"])
        actions.grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky="e")
        tk.Button(
            actions,
            text="Edit",
            command=lambda task_id=task["id"]: self.open_task_editor(task_id),
            bg=THEME["panel_alt"],
            fg=THEME["primary_dark"],
            bd=0,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
        ).pack(side="left", padx=(0, 10))
        tk.Button(
            actions,
            text="🗑",
            command=lambda task_id=task["id"]: self.delete_task(task_id),
            bg=THEME["accent_rose"],
            fg=THEME["primary_dark"],
            bd=0,
            relief="flat",
            font=("Segoe UI", 10),
            padx=8,
            pady=3,
        ).pack(side="left")

        drag_handle = tk.Label(
            actions,
            text="⋮⋮",
            bg=THEME["panel_bg"],
            fg=THEME["muted"],
            font=("Segoe UI", 11, "bold"),
            cursor="fleur",
            padx=6,
        )
        drag_handle.pack(side="left", padx=(10, 0))

        row.columnconfigure(1, weight=1)

        drag_handle.bind("<ButtonPress-1>", lambda event, drag_row=row, drag_parent=parent: self.begin_task_drag(event, drag_row, drag_parent), add="+")
        drag_handle.bind("<B1-Motion>", self.on_task_drag_motion, add="+")
        drag_handle.bind("<ButtonRelease-1>", self.finish_task_drag, add="+")

    def begin_task_drag(self, _event: tk.Event, row: tk.Widget, parent: tk.Widget) -> None:
        self.dragged_task_id = int(getattr(row, "_task_id"))
        self.dragged_task_parent = parent
        self.dragged_row = row
        row.configure(highlightbackground=THEME["primary_light"])

    def on_task_drag_motion(self, event: tk.Event) -> None:
        if not hasattr(self, "dragged_row") or self.dragged_row is None:
            return
        if self.dragged_task_parent is None:
            return

        parent = self.dragged_task_parent
        row = self.dragged_row
        rows = [child for child in parent.winfo_children() if getattr(child, "_task_id", None) is not None]
        if len(rows) < 2 or row not in rows:
            return

        other_rows = [item for item in rows if item is not row]
        insert_before: tk.Widget | None = None
        for candidate in other_rows:
            midpoint = candidate.winfo_rooty() + (candidate.winfo_height() / 2)
            if event.y_root < midpoint:
                insert_before = candidate
                break

        current_index = rows.index(row)
        if insert_before is not None:
            target_index = rows.index(insert_before)
            if target_index != current_index:
                row.pack_forget()
                row.pack(fill="x", pady=6, before=insert_before)
        else:
            if current_index != len(rows) - 1:
                row.pack_forget()
                row.pack(fill="x", pady=6, after=rows[-1])

    def finish_task_drag(self, _event: tk.Event) -> None:
        if not hasattr(self, "dragged_row") or self.dragged_row is None:
            return
        if self.dragged_task_parent is None:
            return

        dragged = self.dragged_row
        dragged.configure(highlightbackground=THEME["line"])

        parent = self.dragged_task_parent
        ordered = [
            int(getattr(child, "_task_id"))
            for child in parent.winfo_children()
            if getattr(child, "_task_id", None) is not None
        ]
        self.store.reorder_tasks(ordered)
        self.status_var.set("Task order updated.")

        self.dragged_row = None
        self.dragged_task_parent = None
        self.dragged_task_id = None

    def task_status_text(self, task: sqlite3.Row) -> str:
        today = date.today().isoformat()
        due_date = task["next_due_date"] or today
        repeat_rule = task["repeat_rule"] or "daily"

        if task["completed_today"]:
            if repeat_rule == "once":
                return "Completed"
            if due_date > today:
                return f"Completed early for {due_date}"
            if due_date == today:
                return "Completed today"
            return "Completed"

        if due_date > today:
            return f"Next {due_date}"
        if due_date < today:
            return "Overdue"
        return "Due today"

    def on_task_toggle(self, task_id: int, checked: bool) -> None:
        self.store.set_completed(task_id, checked)
        self.status_var.set("Task updated.")
        self.refresh_tasks()

    def add_task(self) -> None:
        title = self.normalize_task_title(self.task_title_var.get())
        selected_date_text = self.task_date_var.get().strip()
        repeat_label = self.repeat_var.get().strip()
        repeat_rule = REPEAT_TO_RULE.get(repeat_label, "daily")

        if not title:
            ThemedDialog.show(self.root, "Missing task", "Enter a task title.", kind="warning")
            return

        try:
            selected_date = datetime.strptime(selected_date_text, "%Y-%m-%d").date()
        except ValueError:
            ThemedDialog.show(self.root, "Invalid date", "Pick a valid date.", kind="warning")
            return

        hour_text = self.normalize_time_input(self.task_hour_var.get(), TIME_PLACEHOLDERS["hour"])
        minute_text = self.normalize_time_input(self.task_minute_var.get(), TIME_PLACEHOLDERS["minute"])
        meridiem_text = self.normalize_time_input(self.task_meridiem_var.get(), TIME_PLACEHOLDERS["meridiem"]).upper()
        time_parts = [hour_text, minute_text, meridiem_text]
        all_day = not any(time_parts)
        reminder_time = "00:00"
        if not all_day:
            if not all(part for part in time_parts):
                ThemedDialog.show(self.root, "Invalid time", "Leave all time fields blank or fill all of them.", kind="warning")
                return
            try:
                reminder_time = display_to_time(hour_text, minute_text, meridiem_text)
            except ValueError:
                ThemedDialog.show(self.root, "Invalid time", "Enter a valid time using 1-12, 00-59, and AM or PM.", kind="warning")
                return

        self.store.add_task(title, reminder_time, repeat_rule, selected_date, all_day)
        self.task_title_var.set("")
        self.set_task_date(date.today())
        self.reset_time_fields()
        self.repeat_var.set("Once")
        self.status_var.set("Task added.")
        self.refresh_tasks()
        self.focus_task_entry()

    def clear_tasks(self, completed: bool) -> None:
        label = "completed" if completed else "saved"
        if not ThemedDialog.ask_yes_no(self.root, "Clear tasks", f"Delete all {label} tasks?"):
            return
        removed = self.store.delete_tasks_by_completion(completed)
        self.status_var.set(f"Cleared {removed} {label} tasks.")
        self.refresh_tasks()

    def open_task_editor(self, task_id: int) -> None:
        task = self.store.task_by_id(task_id)
        if task is None:
            return

        editor = tk.Toplevel(self.root)
        editor.title("Edit Task")
        editor.resizable(False, False)
        editor.configure(bg=THEME["panel_bg"])
        editor.transient(self.root)
        editor.grab_set()
        apply_window_icons(editor)

        wrapper = tk.Frame(editor, bg=THEME["panel_bg"], padx=18, pady=16)
        wrapper.pack(fill="both", expand=True)
        tk.Label(wrapper, text="Edit task", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 14, "bold")).pack(anchor="w")

        title_var = tk.StringVar(value=task["title"])
        date_var = tk.StringVar(value=task["next_due_date"] or date.today().isoformat())
        date_display_var = tk.StringVar(value=self.format_date_for_display(datetime.strptime(date_var.get(), "%Y-%m-%d").date()))
        repeat_var = tk.StringVar(value=RULE_TO_REPEAT.get(task["repeat_rule"] or "daily", "Daily"))

        if int(task["all_day"] or 0):
            hour_var = tk.StringVar(value=TIME_PLACEHOLDERS["hour"])
            minute_var = tk.StringVar(value=TIME_PLACEHOLDERS["minute"])
            meridiem_var = tk.StringVar(value=TIME_PLACEHOLDERS["meridiem"])
        else:
            current_time = task["reminder_time"] or "12:00"
            hour_24, minute = current_time.split(":")
            hour_24_int = int(hour_24)
            meridiem_var = tk.StringVar(value="AM" if hour_24_int < 12 else "PM")
            hour_12 = hour_24_int % 12 or 12
            hour_var = tk.StringVar(value=str(hour_12))
            minute_var = tk.StringVar(value=minute)

        form = tk.Frame(wrapper, bg=THEME["panel_bg"])
        form.pack(fill="x", pady=(14, 0))

        title_row = tk.Frame(form, bg=THEME["panel_bg"])
        title_row.pack(fill="x")
        title_entry = tk.Entry(title_row, textvariable=title_var, font=("Segoe UI", 11), bg="white", fg=THEME["text"], insertbackground=THEME["text"], relief="solid", bd=1, highlightthickness=1, highlightbackground=THEME["line"], highlightcolor=THEME["primary_light"])
        title_entry.pack(side="left", fill="x", expand=True, ipady=8)
        title_entry.bind("<KeyRelease>", lambda _event: self._capitalize_var(title_var))

        second_row = tk.Frame(form, bg=THEME["panel_bg"])
        second_row.pack(fill="x", pady=(12, 0))
        date_box = tk.Frame(second_row, bg=THEME["panel_bg"])
        date_box.pack(side="left", padx=(0, 10))
        tk.Label(date_box, text="Date", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10)).pack(anchor="w")
        date_button = tk.Button(
            date_box,
            textvariable=date_display_var,
            command=lambda: self.open_edit_date_picker(date_var, date_display_var, editor),
            bg=THEME["panel_alt"],
            fg=THEME["text"],
            activebackground=THEME["sidebar_active"],
            activeforeground=THEME["text"],
            bd=0,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=7,
            anchor="w",
        )
        date_button.pack(anchor="w", pady=(2, 0))

        time_box = tk.Frame(second_row, bg=THEME["panel_bg"])
        time_box.pack(side="left", padx=(0, 8))
        tk.Label(time_box, text="Time (optional)", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10)).pack(anchor="w")
        time_row = tk.Frame(time_box, bg=THEME["panel_bg"])
        time_row.pack(anchor="w", pady=(2, 0))
        ThemedPicker(time_row, hour_var, [str(hour) for hour in range(1, 13)], width=5).pack(side="left")
        tk.Label(time_row, text=":", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 11)).pack(side="left", padx=4)
        ThemedPicker(time_row, minute_var, [f"{minute:02d}" for minute in range(60)], width=4).pack(side="left")
        ThemedPicker(time_row, meridiem_var, ["AM", "PM"], width=7).pack(side="left", padx=(6, 0))

        repeat_box = tk.Frame(second_row, bg=THEME["panel_bg"])
        repeat_box.pack(side="left", padx=(0, 6))
        tk.Label(repeat_box, text="Repeat", bg=THEME["panel_bg"], fg=THEME["text"], font=("Segoe UI", 10)).pack(anchor="w")
        ThemedPicker(repeat_box, repeat_var, REPEAT_OPTIONS, width=12).pack(anchor="w", pady=(2, 0))

        button_row = tk.Frame(wrapper, bg=THEME["panel_bg"])
        button_row.pack(fill="x", pady=(16, 0))

        def save_edit() -> None:
            title = title_var.get().strip()
            if not title:
                ThemedDialog.show(editor, "Missing task", "Enter a task title.", kind="warning")
                return
            try:
                selected_date = datetime.strptime(date_var.get().strip(), "%Y-%m-%d").date()
            except ValueError:
                ThemedDialog.show(editor, "Invalid date", "Pick a valid date.", kind="warning")
                return

            title = self.normalize_task_title(title)
            time_parts = [
                self.normalize_time_input(hour_var.get(), TIME_PLACEHOLDERS["hour"]),
                self.normalize_time_input(minute_var.get(), TIME_PLACEHOLDERS["minute"]),
                self.normalize_time_input(meridiem_var.get(), TIME_PLACEHOLDERS["meridiem"]),
            ]
            all_day = not any(time_parts)
            reminder_time = "00:00"
            if not all_day:
                if not all(part for part in time_parts):
                    ThemedDialog.show(editor, "Invalid time", "Leave all time fields blank or fill all of them.", kind="warning")
                    return
                try:
                    reminder_time = display_to_time(time_parts[0], time_parts[1], time_parts[2])
                except ValueError:
                    ThemedDialog.show(editor, "Invalid time", "Enter a valid time using 1-12, 00-59, and AM or PM.", kind="warning")
                    return

            self.store.update_task(task_id, title, reminder_time, REPEAT_TO_RULE.get(repeat_var.get().strip(), "daily"), selected_date, all_day)
            self.status_var.set("Task updated.")
            self.refresh_tasks()
            editor.destroy()

        tk.Button(button_row, text="Save", command=save_edit, bg=THEME["primary"], fg="white", bd=0, relief="flat", font=("Segoe UI", 10, "bold"), padx=18, pady=8).pack(side="right")
        tk.Button(button_row, text="Cancel", command=editor.destroy, bg=THEME["panel_alt"], fg=THEME["text"], bd=0, relief="flat", font=("Segoe UI", 10, "bold"), padx=18, pady=8).pack(side="right", padx=(0, 10))

    def delete_task(self, task_id: int) -> None:
        if not ThemedDialog.ask_yes_no(self.root, "Delete task", "Remove this task permanently?"):
            return
        self.store.delete_task(task_id)
        self.status_var.set("Task deleted.")
        self.refresh_tasks()

    def schedule_checks(self) -> None:
        if not self.show_ui:
            write_background_heartbeat()
        log_debug(f"schedule_checks: ui={self.show_ui} bg_running={background_process_is_running()}")
        self.check_due_tasks()
        self.root.after(CHECK_INTERVAL_MS, self.schedule_checks)

    def minimize_app(self) -> None:
        self.root.iconify()

    def restore_app(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def check_due_tasks(self) -> None:
        if self.reminder_dialog is not None:
            return

        # If the UI is visible and a background process is running, let the
        # background process handle reminders to avoid duplicates.
        if self.show_ui and background_process_is_running():
            log_debug("check_due_tasks: skipped because healthy background worker is active")
            return

        today = date.today().isoformat()
        current_time = datetime.now().strftime(TIME_FORMAT)
        log_debug(f"check_due_tasks: today={today} time={current_time} (bg_running={background_process_is_running()})")
        due_tasks = self.store.due_tasks(today, current_time)
        log_debug(f"check_due_tasks: found {len(due_tasks)} due tasks")

        if not due_tasks:
            return

        self.root.bell()
        self.reminder_dialog = ReminderDialog(self, due_tasks)
        log_debug(f"check_due_tasks: opened reminder dialog for {[t['id'] for t in due_tasks]}")

    def on_close(self) -> None:
        self.minimize_app()
        if self.show_ui:
            self.status_var.set("App is minimized and still running for reminders.")

    def exit_app(self) -> None:
        stop_background_worker()
        self.store.close()
        self.root.destroy()


def main() -> None:
    ensure_app_icon_file()
    if restore_existing_window():
        return

    root = tk.Tk()
    background_mode = BACKGROUND_FLAG in sys.argv

    if background_mode:
        app = None
        try:
            BACKGROUND_PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
            write_background_heartbeat()
            log_debug(f"background mode: pid written {os.getpid()}")
            app = TodoApp(root, show_ui=False, window_title=f"{WINDOW_TITLE} Background")
            root.withdraw()
            root.mainloop()
        finally:
            try:
                BACKGROUND_PID_FILE.unlink()
            except FileNotFoundError:
                pass
            if app is not None:
                try:
                    app.store.close()
                except Exception:
                    pass
            try:
                BACKGROUND_HEARTBEAT_FILE.unlink()
            except FileNotFoundError:
                pass
        return

    start_background_worker()
    log_debug("main: started UI and requested background worker")
    TodoApp(root, show_ui=True)
    root.mainloop()


if __name__ == "__main__":
    main()

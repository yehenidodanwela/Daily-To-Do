# Daily To Do

Desktop to-do app built with Python and Tkinter, packaged as a Windows `.exe`.

## Features

- Add tasks with title, date, optional time, and repeat rule.
- Repeat options: Once, Daily, Weekly, Monthly, Annually.
- Calendar popup for date selection.
- Time selection with Hour/Minute/AM-PM dropdowns.
- Task sections for saved and completed tasks.
- Reminder popup with `OK` and `Mark as complete` actions.
- Drag-and-drop reordering for task rows using the handle on each task.
- Theme switcher with multiple color themes.

## Run

Double-click `dist\Daily To Do.exe`.

## Build

Install dependencies:

```powershell
py -3 -m pip install pillow pyinstaller
```

Build using the canonical spec file:

```powershell
py -3 -m PyInstaller --clean DailyTodo.spec
```

Output executable:

- `dist\Daily To Do.exe`

## Project files

- Entry point: `main.py`
- Build spec (canonical): `DailyTodo.spec`
- App icon source image: `assets\images\5.png`
- Generated build icon: `build\Daily To Do.ico`

## Data storage

The app uses a per-user database under `%APPDATA%\DailyTodo\todo_app.db`.

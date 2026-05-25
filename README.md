# Daily To Do

Desktop to-do app built with Python and Tkinter, packaged as a Windows `.exe`.

## Download

- Latest release: [Daily To Do v1.0.2](https://github.com/yehenidodanwela/Daily-To-Do/releases/tag/v1.0.2)
- The release ZIP includes the Windows executable and all required app files.

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

You do not need Python installed to run the packaged `.exe`.

## How to Use

1. Download the release ZIP file from GitHub.
2. Extract the ZIP to any folder on your Windows PC.
3. Open the extracted folder and double-click `Daily To Do.exe`.
4. If Windows shows a security warning, click `More info` and then `Run anyway`.
5. Add your tasks in the app and close it when you are done.
6. Your tasks are saved locally on your PC, so they will still be there next time you open the app.

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

# Manim GUI + Web Studio

A modern toolset for creating Manim animations with:
- 🖥️ **Desktop app** (`manimgui.py`, PyQt6)
- 🌐 **Web app** (`manimgui_web.py`, Streamlit)

---

## Features

### Shared workflow
- Edit Manim scene code
- Auto-detect scene classes
- Render with selectable quality/output mode
- View structured render logs

### Web Studio highlights
- Better web UI layout (editor + logs + output panel)
- Log filtering (`All`, `Info`, `Warnings+`, `Errors`)
- Download logs as a file
- Shows latest output file and output folder path
- Single-command launch for browser-based interaction

---

## Quick Start

### 1) Install (One-click)

#### Linux / macOS (one command)
```bash
curl -sL https://raw.githubusercontent.com/tereachar134/manimgui/main/install.sh | bash
```

#### Windows PowerShell (one command)
```powershell
irm https://raw.githubusercontent.com/tereachar134/manimgui/main/install.ps1 | iex
```

### 2) Install (Manual commands)

#### Linux / macOS manual
```bash
git clone https://github.com/tereachar134/manimgui.git
cd manimgui
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows manual (PowerShell)
```powershell
git clone https://github.com/tereachar134/manimgui.git
cd manimgui
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3) Run (Desktop)

```bash
python manimgui.py
```

### 4) Run (Web, one command)

```bash
streamlit run manimgui_web.py
```

Then open the local URL shown by Streamlit (usually `http://localhost:8501`).

### 5) Other useful manual commands

```bash
# verify Python syntax quickly
python -m py_compile manimgui.py manimgui_web.py

# run desktop app
python manimgui.py

# run web app
streamlit run manimgui_web.py
```

---

## Web Usage

1. Set your **project directory** in the sidebar.
2. Select a `.py` file (or create/save one from editor content).
3. Enter/select your `Scene` class.
4. Choose quality and output format.
5. Click **Render Scene**.
6. Watch filtered logs and download them when needed.

---

## Requirements

- Python 3.9+
- FFmpeg (required by Manim)
- Cairo / LaTeX dependencies required by your Manim setup

Python packages are in `requirements.txt`.

---

## Notes

- `QAction` import is PyQt6-compatible (`QtGui`).
- Web rendering invokes your local `manim` binary in the selected project directory.

---

## License

MIT

# Manim GUI + Web Studio

Create and render Manim animations with either:
- 🖥️ **Desktop app** (`manimgui.py`, PyQt6)
- 🌐 **Web app** (`manimgui_web.py`, Streamlit)

---

## Features

### Shared workflow
- Edit Manim code
- Auto-detect `Scene` classes
- Render with quality/output presets
- View detailed render logs

### Web Studio highlights
- Two-pane layout (editor + logs/output)
- Log filtering (`All`, `Info`, `Warnings+`, `Errors`)
- Download logs as `.txt`
- Shows latest output file/folder
- Finds Python files in nested folders
- **Update from GitHub** button in sidebar
- **Deep Error Scan** button to detect unresolved merge markers and Python syntax issues

### Desktop highlights
- Rich PyQt editor interface with project explorer
- Log panel with filter, copy-all, copy-selected, export, clear
- Open output file + output folder buttons
- **Update App** button in top bar (`git pull --ff-only`)

---

## Quick Start

### 1) Install (one-click)

#### Linux / macOS
```bash
curl -sL https://raw.githubusercontent.com/tereachar134/manimgui/main/install.sh | bash
```

#### Windows PowerShell
```powershell
irm https://raw.githubusercontent.com/tereachar134/manimgui/main/install.ps1 | iex
```

### 2) Install (manual)

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

### 3) Run desktop
```bash
python manimgui.py
```

### 4) Run web (one command)
```bash
streamlit run manimgui_web.py
```

Then open the local URL shown by Streamlit (usually `http://localhost:8501`).

### 5) Useful commands
```bash
# syntax check
python -m py_compile manimgui.py manimgui_web.py

# run desktop
python manimgui.py

# run web
streamlit run manimgui_web.py
```

---

## Web Usage
1. Set **project directory** in sidebar.
2. Select a `.py` file (or create one by saving editor content).
3. Enter/select your `Scene` class.
4. Choose quality + output.
5. Click **Render Scene**.
6. Use log filter/download as needed.
7. Use **Update from GitHub** to pull latest code.

---

## Requirements
- Python 3.9+
- FFmpeg
- Cairo / LaTeX dependencies required by Manim

Python packages are listed in `requirements.txt`.

---

## License
MIT

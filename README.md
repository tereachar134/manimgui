# Manim GUI + Web Studio

  codex/improve-logging-system-and-ui-wjiw0z
Create and render Manim animations with either:
 
  codex/improve-logging-system-and-ui-gcwvxn
Create and render Manim animations with either:
 A modern toolset for creating Manim animations with:
  main
  main
- 🖥️ **Desktop app** (`manimgui.py`, PyQt6)
- 🌐 **Web app** (`manimgui_web.py`, Streamlit)

---

## Features
  codex/improve-logging-system-and-ui-wjiw0z
 
  codex/improve-logging-system-and-ui-gcwvxn
  main

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
  codex/improve-logging-system-and-ui-wjiw0z
- **Deep Error Scan** button to detect unresolved merge markers
 
  main

### Desktop highlights
- Rich PyQt editor interface with project explorer
- Log panel with filter, copy-all, copy-selected, export, clear
- Open output file + output folder buttons
- **Update App** button in top bar (`git pull --ff-only`)
  codex/improve-logging-system-and-ui-wjiw0z
 
 
  main

### Shared workflow
- Edit Manim scene code
- Auto-detect scene classes
- Render with selectable quality/output mode
- View structured render logs

  codex/improve-logging-system-and-ui-gcwvxn
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
 
### Web Studio highlights
- Better web UI layout (editor + logs + output panel)
- Log filtering (`All`, `Info`, `Warnings+`, `Errors`)
- Download logs as a file
- Shows latest output file and output folder path
- Single-command launch for browser-based interaction
  main

---

## Quick Start

  codex/improve-logging-system-and-ui-wjiw0z
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
 
### 1) Install

  main
  main
```bash
git clone https://github.com/tereachar134/manimgui.git
cd manimgui
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
  codex/improve-logging-system-and-ui-wjiw0z
 
  codex/improve-logging-system-and-ui-gcwvxn
  main

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
  codex/improve-logging-system-and-ui-wjiw0z
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
 
  main
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
 

### 2) Run (Desktop)

```bash
python manimgui.py
```

### 3) Run (Web, one command)

```bash
streamlit run manimgui_web.py
  main
```

Then open the local URL shown by Streamlit (usually `http://localhost:8501`).

---

## Web Usage
  codex/improve-logging-system-and-ui-wjiw0z
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
 

1. Set your **project directory** in the sidebar.
2. Select a `.py` file (or create/save one from editor content).
3. Enter/select your `Scene` class.
4. Choose quality and output format.
5. Click **Render Scene**.
6. Watch filtered logs and download them when needed.

---

  codex/improve-logging-system-and-ui-gcwvxn
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
 
## Requirements

- Python 3.9+
- FFmpeg (required by Manim)
- Cairo / LaTeX dependencies required by your Manim setup

Python packages are in `requirements.txt`.

---

## Notes

- `QAction` import is PyQt6-compatible (`QtGui`).
- Web rendering invokes your local `manim` binary in the selected project directory.
  main

---

## License
  codex/improve-logging-system-and-ui-gcwvxn
 

  main
  main
MIT

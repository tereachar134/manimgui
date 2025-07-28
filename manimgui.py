import sys
import os
import re
import subprocess
try:
    from PyQt6.QtWidgets import QFileSystemModel
except ImportError:
    from PyQt6.QtGui import QFileSystemModel

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
    QPushButton, QTabWidget, QTextEdit, QLabel, QLineEdit, QMessageBox,
    QProgressBar, QToolButton, QInputDialog, QSplitter,
    QTreeView, QComboBox
)
from PyQt6.QtCore import Qt, QProcess, QTimer, QDir, QUrl
from PyQt6.QtGui import (
    QTextCursor, QColor, QTextCharFormat, QIcon, QFont, QSyntaxHighlighter,
    QDesktopServices
)

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.highlighting_rules = []

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c586c0"))  # Magenta
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "\bfrom\b", "\bimport\b", "\bclass\b", "\bdef\b",
            "\bself\b", "\breturn\b", "\bfor\b", "\bin\b",
            "\bwhile\b", "\bif\b", "\belif\b", "\belse\b",
            "\bpass\b", "\bcontinue\b", "\bbreak\b", "\btry\b",
            "\bexcept\b", "\bfinally\b", "\bwith\b", "\bas\b",
            "\bassert\b", "\bdel\b", "\bglobal\b", "\bnonlocal\b",
            "\blambda\b", "\byield\b", "\bTrue\b", "\bFalse\b", "\bNone\b"
        ]
        self.highlighting_rules.extend([(re.compile(pattern), keyword_format) for pattern in keywords])

        # Manim-specific classes format
        manim_format = QTextCharFormat()
        manim_format.setForeground(QColor("#4ec9b0")) # Teal
        manim_classes = [
            "\bScene\b", "\bMobject\b", "\bVMobject\b", "\bText\b",
            "\bWrite\b", "\bCreate\b", "\bFadeIn\b", "\bFadeOut\b",
            "\bCircle\b", "\bSquare\b", "\bLine\b", "\bDot\b",
            "\bArrow\b", "\bVector\b", "\bMatrix\b", "\bTable\b",
            "\bplay\b", "\bwait\b", "\badd\b", "\bremove\b"
        ]
        self.highlighting_rules.extend([(re.compile(pattern), manim_format) for pattern in manim_classes])

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))  # Orange
        self.highlighting_rules.append((re.compile("\".*\""), string_format))
        self.highlighting_rules.append((re.compile(r"'.*'", re.DOTALL), string_format))

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))  # Green
        self.highlighting_rules.append((re.compile("#[^\n]*"), comment_format))

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8")) # Light Green
        self.highlighting_rules.append((re.compile(r"\b[0-9]+\.?[0-9]*\b"), number_format))

        # Decorator format
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#dcdcaa")) # Yellow
        self.highlighting_rules.append((re.compile(r"^\s*@\w+"), decorator_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = pattern
            for match in expression.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class ManimGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manim GUI Editor")
        self.setMinimumSize(1200, 800)

        # Set window flags to ensure proper window decorations and behavior
        flags = Qt.WindowType.Window
        flags |= Qt.WindowType.WindowMinMaxButtonsHint
        flags |= Qt.WindowType.WindowCloseButtonHint
        self.setWindowFlags(flags)

        self.setWindowIcon(QIcon.fromTheme("application-x-python"))
        self.project_path = ""
        self.scene_tabs = {}
        self.render_process = None
        self.animation_count = 0
        self.completed_animations = 0
        self.last_output_path = ""
        self.init_ui()
        self.apply_stylesheet()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Top bar (Project selection + new file)
        top_bar = QHBoxLayout()
        self.project_label = QLabel("📂 No project selected")
        select_btn = QPushButton("Select Project Folder")
        select_btn.clicked.connect(self.select_project)

        new_file_btn = QPushButton("➕ New Scene File")
        new_file_btn.clicked.connect(self.create_new_file)

        fullscreen_btn = QPushButton("Toggle Fullscreen")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)

        top_bar.addWidget(self.project_label)
        top_bar.addStretch()
        top_bar.addWidget(select_btn)
        top_bar.addWidget(new_file_btn)
        top_bar.addWidget(fullscreen_btn)
        layout.addLayout(top_bar)

        # Main content splitter
        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Left side: File Explorer ---
        explorer_container = QWidget()
        explorer_layout = QVBoxLayout(explorer_container)
        explorer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries)
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.doubleClicked.connect(self.file_tree_double_clicked)
        self.file_tree.setHeaderHidden(True)
        for i in range(1, self.file_model.columnCount()):
            self.file_tree.hideColumn(i)

        explorer_layout.addWidget(self.file_tree)
        h_splitter.addWidget(explorer_container)

        # --- Right side: Editor and Output ---
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(0, 0, 0, 0)

        v_splitter = QSplitter(Qt.Orientation.Vertical)

        # Editor tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)
        v_splitter.addWidget(self.tabs)

        # Output log area
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        log_controls = QHBoxLayout()
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        
        copy_btn = QToolButton()
        copy_btn.setText("Copy")
        copy_btn.setToolTip("Copy all logs to clipboard")
        copy_btn.clicked.connect(self.copy_logs)

        clear_btn = QToolButton()
        clear_btn.setText("Clear")
        clear_btn.setToolTip("Clear all logs")
        clear_btn.clicked.connect(self.clear_logs)

        log_controls.addWidget(QLabel("Render Output:"))
        log_controls.addStretch()
        log_controls.addWidget(clear_btn)
        log_controls.addWidget(copy_btn)

        log_layout.addLayout(log_controls)
        log_layout.addWidget(self.output_log)
        log_container.setLayout(log_layout)
        v_splitter.addWidget(log_container)
        v_splitter.setSizes([500, 300])

        right_layout.addWidget(v_splitter)
        right_pane.setLayout(right_layout)
        h_splitter.addWidget(right_pane)
        h_splitter.setSizes([200, 1000])

        layout.addWidget(h_splitter)

        # Render controls
        self.render_controls_widget = QWidget()
        render_bar = QHBoxLayout(self.render_controls_widget)
        render_bar.setContentsMargins(0, 0, 0, 0)

        self.scene_class_input = QLineEdit()
        self.scene_class_input.setPlaceholderText("SceneClassName")
        
        detect_btn = QPushButton("🔍 Auto-Detect")
        detect_btn.setToolTip("Detect scene class from current file")
        detect_btn.clicked.connect(self.detect_scene_class)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Low Quality", "High Quality", "4K"])

        self.output_type_combo = QComboBox()
        self.output_type_combo.addItems(["Video", "Image (PNG)", "Image (SVG)"])

        self.render_btn = QPushButton("▶️ Render")
        self.render_btn.clicked.connect(self.render_scene)

        self.stop_render_btn = QPushButton("⏹️ Stop")
        self.stop_render_btn.clicked.connect(self.stop_rendering)
        
        self.open_output_btn = QPushButton("🎬 Open Output")
        self.open_output_btn.clicked.connect(self.open_last_output)
        self.open_output_btn.setEnabled(False)

        render_bar.addWidget(QLabel("Scene Class:"))
        render_bar.addWidget(self.scene_class_input)
        render_bar.addWidget(detect_btn)
        render_bar.addWidget(self.quality_combo)
        render_bar.addWidget(self.output_type_combo)
        render_bar.addWidget(self.render_btn)
        render_bar.addWidget(self.open_output_btn)
        render_bar.addWidget(self.stop_render_btn)
        layout.addWidget(self.render_controls_widget)

        # Progress bar with animation counter
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        
        self.animation_counter = QLabel("Animations: 0/0")
        self.animation_counter.setStyleSheet("font-weight: bold;")
        
        progress_layout.addWidget(self.progress_bar, 4)
        progress_layout.addWidget(self.animation_counter, 1)
        layout.addLayout(progress_layout)

        self.setLayout(layout)

        # Status timer for progress updates
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_progress)
        self.last_progress = 0

        # Create default project folder and file if none exists
        self.create_default_project()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #f8f8f8;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 10pt;
            }
            QTabWidget::pane {
                border-top: 2px solid #3c3c3c;
            }
            QTabBar::tab {
                background: #2b2b2b;
                border: 1px solid #3c3c3c;
                border-bottom-color: #3c3c3c;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 8ex;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background: #3c3c3c;
                border-color: #4f4f4f;
                border-bottom-color: #3c3c3c;
            }
            QTabBar::tab:!selected:hover {
                background: #4a4a4a;
            }
            QPushButton, QToolButton {
                background-color: #4a4a4a;
                border: 1px solid #5a5a5a;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover, QToolButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed, QToolButton:pressed {
                background-color: #6a6a6a;
            }
            QLineEdit, QTextEdit, QTreeView, QComboBox {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 3px;
            }
            QProgressBar {
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                text-align: center;
                background-color: #252526;
                color: #f8f8f8;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
            QSplitter::handle {
                background: #3c3c3c;
            }
            QSplitter::handle:horizontal {
                width: 1px;
            }
            QSplitter::handle:vertical {
                height: 1px;
            }
            QLabel {
                color: #cccccc;
            }
            QTreeView {
                padding: 5px;
            }
            QPushButton#stop_render_btn {
                 background-color: #ff6b6b; color: white;
            }
        """)
        self.output_log.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #f8f8f8;
                font-family: 'Courier New', monospace;
            }
        """)

    def create_default_project(self):
        """Create a default project folder and file if none exists"""
        default_path = os.path.join(os.path.expanduser("~"), "ManimProjects")
        if not os.path.exists(default_path):
            os.makedirs(default_path)
        
        self.project_path = default_path
        self.project_label.setText(f"📂 {os.path.basename(default_path)}")
        self.file_tree.setRootIndex(self.file_model.setRootPath(default_path))
        
        default_file = os.path.join(default_path, "default_scene.py")
        if not os.path.exists(default_file):
            with open(default_file, 'w') as f:
                f.write(self.default_scene_template())
            self.open_scene_file(default_file)

    def file_tree_double_clicked(self, index):
        path = self.file_model.filePath(index)
        if os.path.isfile(path) and path.endswith('.py'):
            self.open_scene_file(path)

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget:
            for filename, (filepath, editor, highlighter) in list(self.scene_tabs.items()):
                if editor == widget:
                    del self.scene_tabs[filename]
                    break
            widget.deleteLater()
            self.tabs.removeTab(index)

    def tab_changed(self, index):
        """When tab changes, try to auto-detect the scene class"""
        if index >= 0:
            self.detect_scene_class()
            self.count_animations()

    def detect_scene_class(self):
        """Attempt to detect the scene class name from the current file"""
        filepath, editor = self.get_current_file_path()
        if not filepath or not editor:
            return

        code = editor.toPlainText()
        pattern = r"class\s+(\w+)\(.*Scene.*\)"
        matches = re.findall(pattern, code)
        
        if matches:
            self.scene_class_input.setText(matches[0])
            self.append_to_log(f"🔍 Auto-detected scene class: {matches[0]}", "info")
        else:
            self.append_to_log("⚠️ Could not auto-detect scene class", "warning")

    def count_animations(self):
        """Count the number of animation tasks in the current file"""
        filepath, editor = self.get_current_file_path()
        if not filepath or not editor:
            return

        code = editor.toPlainText()
        
        # Count self.play() and self.wait() calls
        play_count = len(re.findall(r"\bself\\.play\b", code))
        wait_count = len(re.findall(r"\bself\\.wait\b", code))
        
        self.animation_count = play_count + wait_count
        self.completed_animations = 0
        self.animation_counter.setText(f"Animations: 0/{self.animation_count}")
        
        if self.animation_count > 0:
            self.append_to_log(f"📊 Detected {self.animation_count} animation tasks", "info")

    def select_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.project_path = folder
            self.project_label.setText(f"📂 {os.path.basename(folder)}")
            self.file_tree.setRootIndex(self.file_model.setRootPath(folder))

    def create_new_file(self):
        if not self.project_path:
            QMessageBox.warning(self, "No Project Selected", "Select a project folder first.")
            return

        filename, ok = QInputDialog.getText(self, "New Scene File", "Enter filename (without .py extension):")
        
        if ok and filename:
            # Basic validation for a valid Python module name
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", filename):
                QMessageBox.warning(self, "Invalid Filename", "Please enter a valid Python module name (letters, numbers, underscores, and cannot start with a number).")
                return

            file_path = os.path.join(self.project_path, f"{filename}.py")

            # Check for overwrite
            if os.path.exists(file_path):
                reply = QMessageBox.question(self, 'File Exists', 
                                             f"The file '{filename}.py' already exists.\nDo you want to overwrite it?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                             QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    self.open_scene_file(file_path) # Open the existing file
                    return
            
            try:
                # Use the filename for the class name
                template = self.default_scene_template(class_name=filename)
                with open(file_path, 'w') as f:
                    f.write(template)
                self.open_scene_file(file_path)
            except (IOError, OSError) as e:
                QMessageBox.critical(self, "Error Creating File", f"Could not create the file:\n{e}")

    def open_scene_file(self, filepath):
        for name, (path, editor, _) in self.scene_tabs.items():
            if path == filepath:
                self.tabs.setCurrentWidget(editor)
                return

        tab = QTextEdit()
        tab.setFont(QFont("Courier New", 10))
        with open(filepath, 'r') as f:
            tab.setPlainText(f.read())
        
        highlighter = PythonSyntaxHighlighter(tab.document())

        filename = os.path.basename(filepath)
        self.scene_tabs[filename] = (filepath, tab, highlighter)
        index = self.tabs.addTab(tab, filename)
        self.tabs.setCurrentIndex(index)

    def get_current_file_path(self):
        current_index = self.tabs.currentIndex()
        if current_index == -1:
            return None, None
        tab_name = self.tabs.tabText(current_index)
        if tab_name in self.scene_tabs:
            return self.scene_tabs[tab_name][0], self.scene_tabs[tab_name][1]
        return None, None

    def render_scene(self):
        if self.render_process and self.render_process.state() == QProcess.ProcessState.Running:
            QMessageBox.warning(self, "Render in Progress", "A rendering process is already running. Please wait for it to complete.")
            return

        filepath, editor = self.get_current_file_path()
        if not filepath or not self.project_path:
            QMessageBox.warning(self, "No Scene Selected", "Open or create a scene file first.")
            return

        with open(filepath, 'w') as f:
            f.write(editor.toPlainText())

        scene_class = self.scene_class_input.text().strip()
        if not scene_class:
            QMessageBox.warning(self, "Missing Scene Name", "Enter the SceneClassName to render.")
            return

        quality_map = {"Low Quality": "-ql", "High Quality": "-qh", "4K": "-qk"}
        quality = self.quality_combo.currentText()
        flag = quality_map[quality]
        
        output_type = self.output_type_combo.currentText()
        if output_type == "Video":
            cmd = f"manim -p {flag} \"{filepath}\" {scene_class}"
        elif output_type == "Image (PNG)":
            cmd = f"manim -s {flag} \"{filepath}\" {scene_class}"
        elif output_type == "Image (SVG)":
            cmd = f"manim -s --format=svg {flag} \"{filepath}\" {scene_class}"

        self.output_log.clear()
        self.last_progress = 0
        self.completed_animations = 0
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        self.last_output_path = ""
        self.open_output_btn.setEnabled(False)
        self.animation_counter.setText(f"Animations: 0/{self.animation_count}")
        
        self.append_to_log(f"▶️ Starting render: {cmd}\n", "info")
        
        self.render_process = QProcess()
        self.render_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.render_process.readyReadStandardOutput.connect(self.handle_stdout)
        self.render_process.finished.connect(self.render_finished)
        self.render_process.setWorkingDirectory(self.project_path)
        self.render_process.startCommand(cmd)
        self.status_timer.start(100)
        self.render_controls_widget.setEnabled(False)

    def handle_stdout(self):
        if not self.render_process:
            return
            
        data = self.render_process.readAllStandardOutput().data().decode()
        for line in data.split('\n'):
            if line.strip():
                self.process_output_line(line)

    def process_output_line(self, line):
        if "Animation" in line and "finished" in line:
            self.completed_animations += 1
            progress = int((self.completed_animations / max(1, self.animation_count)) * 100)
            self.last_progress = progress
            self.animation_counter.setText(f"Animations: {self.completed_animations}/{self.animation_count}")
            self.progress_bar.setValue(progress)
        
        elif "Animation" in line and ":" in line and "%" in line:
            try:
                anim_part = line.split("Animation")[1].split(":")[0].strip()
                anim_num = int(anim_part) if anim_part.isdigit() else self.completed_animations
                percent_part = line.split("%")[0].split(":")[-1].strip()
                anim_progress = float(percent_part)
                
                if self.animation_count > 0:
                    anim_weight = 100 / self.animation_count
                    base_progress = anim_num * anim_weight
                    current_anim_progress = (anim_progress / 100) * anim_weight
                    total_progress = base_progress + current_anim_progress
                    self.last_progress = int(total_progress)
                    self.progress_bar.setValue(self.last_progress)
            except (ValueError, IndexError, AttributeError):
                pass
        
        elif "File ready at" in line:
            match = re.search(r"File ready at:\s*(.*\\.(mp4|png|svg))", line)
            if match:
                # Manim gives a relative path, make it absolute
                relative_path = match.group(1).strip()
                self.last_output_path = os.path.join(self.project_path, relative_path)
                self.append_to_log(f"🎥 Output available at: {self.last_output_path}", "info")

        if "INFO" in line: self.append_to_log(line, "info")
        elif "WARNING" in line: self.append_to_log(line, "warning")
        elif "ERROR" in line or "Exception" in line: self.append_to_log(line, "error")
        else: self.append_to_log(line, "normal")

    def append_to_log(self, text, msg_type):
        cursor = self.output_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        format = QTextCharFormat()
        if msg_type == "error": format.setForeground(QColor("#ff4444")); format.setFontWeight(75)
        elif msg_type == "warning": format.setForeground(QColor("#ffbb33"))
        elif msg_type == "info": format.setForeground(QColor("#33b5e5"))
        else: format.setForeground(QColor("#f8f8f8"))
        
        cursor.setCharFormat(format)
        cursor.insertText(text + "\n")
        self.output_log.ensureCursorVisible()

    def update_progress(self):
        self.progress_bar.setValue(self.last_progress)

    def render_finished(self, exit_code, exit_status):
        self.status_timer.stop()
        self.render_controls_widget.setEnabled(True)
        
        if exit_code == 0:
            self.append_to_log("✅ Render completed successfully!", "info")
            self.progress_bar.setValue(100)
            if self.last_output_path:
                self.open_output_btn.setEnabled(True)
            self.animation_counter.setText(f"Animations: {self.animation_count}/{self.animation_count}")
        else:
            self.append_to_log(f"❌ Render failed with exit code {exit_code}", "error")
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ff4444; }")
        
        self.render_process = None

    def stop_rendering(self):
        if self.render_process and self.render_process.state() == QProcess.ProcessState.Running:
            self.render_process.terminate()
            self.append_to_log("🛑 Render process stopped by user", "warning")
            self.progress_bar.setValue(0)
            self.status_timer.stop()
            self.render_controls_widget.setEnabled(True)

    def open_last_output(self):
        if self.last_output_path and os.path.exists(self.last_output_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_output_path))
        else:
            QMessageBox.warning(self, "File Not Found", f"Could not find the output file:\n{self.last_output_path}")

    def copy_logs(self):
        QApplication.clipboard().setText(self.output_log.toPlainText())
        self.append_to_log("📋 Logs copied to clipboard", "info")

    def clear_logs(self):
        self.output_log.clear()

    def default_scene_template(self, class_name="MyScene"):
        # Sanitize class_name to be a valid identifier
        safe_class_name = re.sub(r'\W|^(?=\d)', '_', class_name)
        if not safe_class_name:
            safe_class_name = "MyScene"

        return f'''from manim import *

class {safe_class_name}(Scene):
    def construct(self):
        # Create a sample animation
        circle = Circle()
        square = Square()

        self.play(Create(square))
        self.play(Transform(square, circle))
        self.play(FadeOut(square))
        self.wait()
'''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Manim GUI")
    window = ManimGUI()
    window.show()
    sys.exit(app.exec())

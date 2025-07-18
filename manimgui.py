import sys
import os
import re
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
    QPushButton, QTabWidget, QTextEdit, QLabel, QLineEdit, QMessageBox,
    QProgressBar, QToolButton, QInputDialog
)
from PyQt6.QtCore import Qt, QProcess, QTimer
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QIcon

class ManimGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manim GUI Editor")
        self.setMinimumSize(1000, 700)
        self.project_path = ""
        self.scene_tabs = {}
        self.render_process = None
        self.animation_count = 0
        self.completed_animations = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Top bar (Project selection + new file)
        top_bar = QHBoxLayout()
        self.project_label = QLabel("📂 No project selected")
        select_btn = QPushButton("Select Project Folder")
        select_btn.clicked.connect(self.select_project)

        new_file_btn = QPushButton("➕ New Scene File")
        new_file_btn.clicked.connect(self.create_new_file)

        top_bar.addWidget(self.project_label)
        top_bar.addStretch()
        top_bar.addWidget(select_btn)
        top_bar.addWidget(new_file_btn)
        layout.addLayout(top_bar)

        # Tab editor
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.tab_changed)
        layout.addWidget(self.tabs)

        # Render controls
        render_bar = QHBoxLayout()
        self.scene_class_input = QLineEdit()
        self.scene_class_input.setPlaceholderText("SceneClassName")
        
        # Auto-detect button
        detect_btn = QPushButton("🔍 Auto-Detect")
        detect_btn.setToolTip("Detect scene class from current file")
        detect_btn.clicked.connect(self.detect_scene_class)

        render_low_btn = QPushButton("▶️ Low")
        render_low_btn.clicked.connect(lambda: self.render_scene("low"))

        render_high_btn = QPushButton("▶️ High")
        render_high_btn.clicked.connect(lambda: self.render_scene("high"))

        render_4k_btn = QPushButton("▶️ 4K")
        render_4k_btn.clicked.connect(lambda: self.render_scene("4k"))

        stop_render_btn = QPushButton("⏹️ Stop")
        stop_render_btn.clicked.connect(self.stop_rendering)
        stop_render_btn.setStyleSheet("background-color: #ff6b6b; color: white;")

        render_bar.addWidget(QLabel("Scene Class:"))
        render_bar.addWidget(self.scene_class_input)
        render_bar.addWidget(detect_btn)
        render_bar.addWidget(render_low_btn)
        render_bar.addWidget(render_high_btn)
        render_bar.addWidget(render_4k_btn)
        render_bar.addWidget(stop_render_btn)

        layout.addLayout(render_bar)

        # Progress bar with animation counter
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)
        
        self.animation_counter = QLabel("Animations: 0/0")
        self.animation_counter.setStyleSheet("font-weight: bold;")
        
        progress_layout.addWidget(self.progress_bar, 4)
        progress_layout.addWidget(self.animation_counter, 1)
        layout.addLayout(progress_layout)

        # Output log with controls
        log_controls = QHBoxLayout()
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #f8f8f8;
                font-family: 'Courier New', monospace;
            }
        """)

        # Copy button for logs
        copy_btn = QToolButton()
        copy_btn.setIcon(QIcon.fromTheme("edit-copy"))
        copy_btn.setToolTip("Copy all logs to clipboard")
        copy_btn.clicked.connect(self.copy_logs)

        # Clear button for logs
        clear_btn = QToolButton()
        clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        clear_btn.setToolTip("Clear all logs")
        clear_btn.clicked.connect(self.clear_logs)

        log_controls.addWidget(QLabel("Render Output:"))
        log_controls.addStretch()
        log_controls.addWidget(clear_btn)
        log_controls.addWidget(copy_btn)

        layout.addLayout(log_controls)
        layout.addWidget(self.output_log)

        self.setLayout(layout)

        # Status timer for progress updates
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_progress)
        self.last_progress = 0

        # Create default project folder and file if none exists
        self.create_default_project()

    def create_default_project(self):
        """Create a default project folder and file if none exists"""
        default_path = os.path.join(os.path.expanduser("~"), "ManimProjects")
        if not os.path.exists(default_path):
            os.makedirs(default_path)
        
        self.project_path = default_path
        self.project_label.setText(f"📂 {os.path.basename(default_path)}")
        
        # Create a default file if none exists
        default_file = os.path.join(default_path, "default_scene.py")
        if not os.path.exists(default_file):
            with open(default_file, 'w') as f:
                f.write(self.default_scene_template())
            self.open_scene_file(default_file)

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

        # Get the text from the editor
        code = editor.toPlainText()
        
        # Try to find class definitions that inherit from Scene
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
        
        # Count self.play() calls (each may contain multiple animations)
        play_pattern = r"self\.play\(([^)]*)\)"
        play_matches = re.findall(play_pattern, code)
        
        # Count self.wait() calls
        wait_pattern = r"self\.wait\("
        wait_count = len(re.findall(wait_pattern, code))
        
        # Estimate animation count (each play might have multiple animations)
        self.animation_count = len(play_matches) + wait_count
        self.completed_animations = 0
        self.animation_counter.setText(f"Animations: 0/{self.animation_count}")
        
        if self.animation_count > 0:
            self.append_to_log(f"📊 Detected {self.animation_count} animation tasks in code", "info")

    def select_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.project_path = folder
            self.project_label.setText(f"📂 {os.path.basename(folder)}")

    def create_new_file(self):
        if not self.project_path:
            QMessageBox.warning(self, "No Project Selected", "Select a project folder first.")
            return

        # Ask only for filename, save in current project folder
        filename, ok = QInputDialog.getText(self, "New Scene File", "Enter filename (without .py extension):")
        if ok and filename:
            file_path = os.path.join(self.project_path, f"{filename}.py")
            with open(file_path, 'w') as f:
                f.write(self.default_scene_template())
            self.open_scene_file(file_path)

    def open_scene_file(self, filepath):
        tab = QTextEdit()
        with open(filepath, 'r') as f:
            tab.setPlainText(f.read())
        filename = os.path.basename(filepath)
        self.scene_tabs[filename] = (filepath, tab)
        self.tabs.addTab(tab, filename)
        
        # Auto-detect scene class when opening file
        self.detect_scene_class()
        self.count_animations()

    def get_current_file_path(self):
        current_index = self.tabs.currentIndex()
        if current_index == -1:
            return None, None
        tab_name = self.tabs.tabText(current_index)
        return self.scene_tabs.get(tab_name, (None, None))

    def render_scene(self, quality):
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

        quality_flags = {
            "low": "-pql",
            "high": "-pqh",
            "4k": "-p --resolution=3840,2160"
        }

        flag = quality_flags[quality]
        cmd = f"manim {flag} \"{filepath}\" {scene_class}"
        
        # Clear previous logs and reset progress
        self.output_log.clear()
        self.last_progress = 0
        self.completed_animations = 0
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        self.animation_counter.setText(f"Animations: 0/{self.animation_count}")
        
        self.append_to_log(f"▶️ Starting render: {cmd}\n", "info")
        
        # Start the process
        self.render_process = QProcess()
        self.render_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.render_process.readyReadStandardOutput.connect(self.handle_stdout)
        self.render_process.finished.connect(self.render_finished)
        
        # Start the process with the command
        self.render_process.startCommand(cmd)
        
        # Start progress update timer
        self.status_timer.start(100)

    def handle_stdout(self):
        if not self.render_process:
            return
            
        data = self.render_process.readAllStandardOutput().data().decode()
        for line in data.split('\n'):
            if line.strip():
                self.process_output_line(line)

    def process_output_line(self, line):
        # Check for animation completion
        if "Animation" in line and "finished" in line:
            self.completed_animations += 1
            progress = int((self.completed_animations / max(1, self.animation_count)) * 100)
            self.last_progress = progress
            self.animation_counter.setText(f"Animations: {self.completed_animations}/{self.animation_count}")
            self.progress_bar.setValue(progress)
        
        # Check for animation progress
        elif "Animation" in line and ":" in line and "%" in line:
            try:
                # Extract the animation number
                anim_part = line.split("Animation")[1].split(":")[0].strip()
                anim_num = int(anim_part) if anim_part.isdigit() else 0
                
                # Extract the progress percentage
                percent_part = line.split("%")[0].split(":")[-1].strip()
                anim_progress = float(percent_part)
                
                # Calculate overall progress
                if self.animation_count > 0:
                    anim_weight = 100 / self.animation_count
                    base_progress = anim_num * anim_weight
                    current_anim_progress = (anim_progress / 100) * anim_weight
                    total_progress = base_progress + current_anim_progress
                    self.last_progress = int(total_progress)
                    self.progress_bar.setValue(self.last_progress)
            except (ValueError, IndexError, AttributeError) as e:
                self.append_to_log(f"⚠️ Progress parsing error: {str(e)}", "warning")
        
        # Check for regular progress indicators
        elif "Rendering frame" in line and "Scene:" in line:
            self.append_to_log(line, "progress")
        elif "INFO" in line:
            self.append_to_log(line, "info")
        elif "WARNING" in line:
            self.append_to_log(line, "warning")
        elif "ERROR" in line or "Exception" in line:
            self.append_to_log(line, "error")
        else:
            self.append_to_log(line, "normal")

    def append_to_log(self, text, msg_type):
        cursor = self.output_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Create format based on message type
        format = QTextCharFormat()
        
        if msg_type == "error":
            format.setForeground(QColor("#ff4444"))
            format.setFontWeight(75)
        elif msg_type == "warning":
            format.setForeground(QColor("#ffbb33"))
        elif msg_type == "info":
            format.setForeground(QColor("#33b5e5"))
        elif msg_type == "progress":
            format.setForeground(QColor("#99cc00"))
        else:  # normal
            format.setForeground(QColor("#f8f8f8"))
        
        cursor.setCharFormat(format)
        cursor.insertText(text + "\n")
        self.output_log.ensureCursorVisible()

    def update_progress(self):
        # Update progress bar with the last known progress
        self.progress_bar.setValue(self.last_progress)
        
        # Change color if progress is stuck
        if self.last_progress > 0 and self.progress_bar.value() == self.last_progress:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #FFA500;
                }
            """)

    def render_finished(self, exit_code, exit_status):
        self.status_timer.stop()
        
        if exit_code == 0:
            self.append_to_log("✅ Render completed successfully!", "info")
            self.progress_bar.setValue(100)
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #4CAF50;
                }
            """)
            self.animation_counter.setText(f"Animations: {self.animation_count}/{self.animation_count}")
        else:
            self.append_to_log(f"❌ Render failed with exit code {exit_code}", "error")
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #ff4444;
                }
            """)
        
        self.render_process = None

    def stop_rendering(self):
        if self.render_process and self.render_process.state() == QProcess.ProcessState.Running:
            self.render_process.terminate()
            self.append_to_log("🛑 Render process stopped by user", "warning")
            self.progress_bar.setValue(0)
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #ff4444;
                }
            """)
            self.status_timer.stop()

    def copy_logs(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_log.toPlainText())
        self.append_to_log("📋 Logs copied to clipboard", "info")

    def clear_logs(self):
        self.output_log.clear()
        self.append_to_log("🧹 Logs cleared", "info")

    def default_scene_template(self):
        return '''from manim import *

class MyScene(Scene):
    def construct(self):
        text = Text("Hello Manim GUI!")
        self.play(Write(text))
        self.wait()
'''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ManimGUI()
    window.show()
    sys.exit(app.exec())

import sys
import os
import re
import subprocess
import json
from datetime import datetime
try:
    from PyQt6.QtWidgets import QFileSystemModel
except ImportError:
    from PyQt6.QtGui import QFileSystemModel

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
    QPushButton, QTabWidget, QTextEdit, QLabel, QLineEdit, QMessageBox,
    QProgressBar, QToolButton, QInputDialog, QSplitter,
    QTreeView, QComboBox, QToolBar, QMenu, QMenuBar,
    QFrame, QScrollArea, QGridLayout, QSizePolicy,
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QCheckBox
)
from PyQt6.QtCore import Qt, QProcess, QTimer, QDir, QUrl, QSettings, QStandardPaths, QSize
from PyQt6.QtGui import (
    QTextCursor, QColor, QTextCharFormat, QIcon, QFont, QSyntaxHighlighter, QAction, QShortcut,
    QDesktopServices, QKeySequence, QPixmap, QMovie
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
            r"\bfrom\b", r"\bimport\b", r"\bclass\b", r"\bdef\b",
            r"\bself\b", r"\breturn\b", r"\bfor\b", r"\bin\b",
            r"\bwhile\b", r"\bif\b", r"\belif\b", r"\belse\b",
            r"\bpass\b", r"\bcontinue\b", r"\bbreak\b", r"\btry\b",
            r"\bexcept\b", r"\bfinally\b", r"\bwith\b", r"\bas\b",
            r"\bassert\b", r"\bdel\b", r"\bglobal\b", r"\bnonlocal\b",
            r"\blambda\b", r"\byield\b", r"\bTrue\b", r"\bFalse\b", r"\bNone\b"
        ]
        self.highlighting_rules.extend([(re.compile(pattern), keyword_format) for pattern in keywords])

        # Manim-specific classes format
        manim_format = QTextCharFormat()
        manim_format.setForeground(QColor("#4ec9b0")) # Teal
        manim_classes = [
            r"\bScene\b", r"\bMobject\b", r"\bVMobject\b", r"\bText\b",
            r"\bWrite\b", r"\bCreate\b", r"\bFadeIn\b", r"\bFadeOut\b",
            r"\bCircle\b", r"\bSquare\b", r"\bLine\b", r"\bDot\b",
            r"\bArrow\b", r"\bVector\b", r"\bMatrix\b", r"\bTable\b",
            r"\bplay\b", r"\bwait\b", r"\badd\b", r"\bremove\b"
        ]
        self.highlighting_rules.extend([(re.compile(pattern), manim_format) for pattern in manim_classes])

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))  # Orange
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

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
        self.setWindowTitle("Manim GUI Editor - Professional")
        self.setMinimumSize(1400, 900)

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
        self.last_output_dir = ""
        self.recent_projects = []
        self.snippets = self.load_snippets()
        self.log_history = []
        self.init_ui()
        self.init_menu_bar()
        self.init_toolbar()
        self.apply_modern_stylesheet()
        self.load_recent_projects()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Modern gradient top bar with project info and quick actions
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 10, 15, 10)
        
        # Project info with icon
        project_info_layout = QHBoxLayout()
        self.project_icon = QLabel("📁")
        self.project_icon.setStyleSheet("font-size: 20px;")
        self.project_label = QLabel("No project selected")
        self.project_label.setObjectName("projectLabel")
        project_info_layout.addWidget(self.project_icon)
        project_info_layout.addWidget(self.project_label)
        
        select_btn = QPushButton("📂 Open Project")
        select_btn.setObjectName("primaryBtn")
        select_btn.clicked.connect(self.select_project)

        new_file_btn = QPushButton("➕ New Scene")
        new_file_btn.setObjectName("actionBtn")
        new_file_btn.clicked.connect(self.create_new_file)

        snippets_btn = QPushButton("📝 Snippets")
        snippets_btn.setObjectName("actionBtn")
        snippets_btn.clicked.connect(self.show_snippets_panel)

        update_btn = QPushButton("🔄 Update App")
        update_btn.setObjectName("actionBtn")
        update_btn.setToolTip("Pull the latest code from GitHub")
        update_btn.clicked.connect(self.update_from_github)

        fullscreen_btn = QToolButton()
        fullscreen_btn.setText("⛶")
        fullscreen_btn.setToolTip("Toggle Fullscreen (F11)")
        fullscreen_btn.setObjectName("iconBtn")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        
        # Keyboard shortcut for fullscreen
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        fullscreen_shortcut.activated.connect(self.toggle_fullscreen)

        top_layout.addLayout(project_info_layout)
        top_layout.addStretch()
        top_layout.addWidget(select_btn)
        top_layout.addWidget(new_file_btn)
        top_layout.addWidget(snippets_btn)
        top_layout.addWidget(update_btn)
        top_layout.addWidget(fullscreen_btn)
        layout.addWidget(top_bar)

        # Main content splitter
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.setObjectName("mainSplitter")

        # --- Left side: File Explorer ---
        explorer_container = QFrame()
        explorer_container.setObjectName("explorerPanel")
        explorer_layout = QVBoxLayout(explorer_container)
        explorer_layout.setContentsMargins(0, 0, 0, 0)
        explorer_layout.setSpacing(5)
        
        # Explorer header
        explorer_header = QLabel("📁 PROJECT FILES")
        explorer_header.setObjectName("panelHeader")
        explorer_layout.addWidget(explorer_header)
        
        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Filter.NoDotAndDotdot | QDir.Filter.AllEntries)
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.doubleClicked.connect(self.file_tree_double_clicked)
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(20)
        for i in range(1, self.file_model.columnCount()):
            self.file_tree.hideColumn(i)

        explorer_layout.addWidget(self.file_tree)
        h_splitter.addWidget(explorer_container)

        # --- Right side: Editor and Output ---
        right_pane = QFrame()
        right_pane.setObjectName("editorPanel")
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.setObjectName("editorSplitter")

        # Editor tabs with enhanced styling
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)
        self.tabs.setObjectName("codeTabs")
        v_splitter.addWidget(self.tabs)

        # Output log area with modern design
        log_container = QFrame()
        log_container.setObjectName("logPanel")
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(5)
        
        # Log header with controls
        log_header_layout = QHBoxLayout()
        log_title = QLabel("📊 RENDER OUTPUT")
        log_title.setObjectName("panelHeader")
        
        copy_btn = QToolButton()
        copy_btn.setText("📋 Copy All")
        copy_btn.setToolTip("Copy all logs to clipboard")
        copy_btn.setObjectName("logBtn")
        copy_btn.clicked.connect(self.copy_logs)

        copy_selected_btn = QToolButton()
        copy_selected_btn.setText("✂️ Copy Selected")
        copy_selected_btn.setToolTip("Copy selected logs")
        copy_selected_btn.setObjectName("logBtn")
        copy_selected_btn.clicked.connect(self.copy_selected_logs)

        clear_btn = QToolButton()
        clear_btn.setText("🗑️ Clear")
        clear_btn.setToolTip("Clear all logs")
        clear_btn.setObjectName("logBtn")
        clear_btn.clicked.connect(self.clear_logs)
        
        export_btn = QToolButton()
        export_btn.setText("💾 Export")
        export_btn.setToolTip("Export logs to file")
        export_btn.setObjectName("logBtn")
        export_btn.clicked.connect(self.export_logs)

        self.log_level_combo = QComboBox()
        self.log_level_combo.setObjectName("logLevelCombo")
        self.log_level_combo.addItems(["All Logs", "Info Only", "Warnings+", "Errors Only"])
        self.log_level_combo.currentIndexChanged.connect(self.refresh_log_display)
        self.log_level_combo.setMinimumWidth(120)

        self.autoscroll_checkbox = QCheckBox("Auto-scroll")
        self.autoscroll_checkbox.setChecked(True)
        self.autoscroll_checkbox.setObjectName("logCheck")

        log_header_layout.addWidget(log_title)
        log_header_layout.addStretch()
        log_header_layout.addWidget(self.log_level_combo)
        log_header_layout.addWidget(self.autoscroll_checkbox)
        log_header_layout.addWidget(export_btn)
        log_header_layout.addWidget(copy_btn)
        log_header_layout.addWidget(copy_selected_btn)
        log_header_layout.addWidget(clear_btn)

        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setObjectName("outputLog")
        
        log_layout.addLayout(log_header_layout)
        log_layout.addWidget(self.output_log)
        log_container.setLayout(log_layout)
        v_splitter.addWidget(log_container)
        v_splitter.setSizes([600, 350])

        right_layout.addWidget(v_splitter)
        right_pane.setLayout(right_layout)
        h_splitter.addWidget(right_pane)
        h_splitter.setSizes([280, 1120])

        layout.addWidget(h_splitter)

        # Enhanced render controls with visual feedback
        self.render_controls_widget = QFrame()
        self.render_controls_widget.setObjectName("renderControls")
        render_bar = QGridLayout(self.render_controls_widget)
        render_bar.setContentsMargins(15, 10, 15, 10)
        render_bar.setHorizontalSpacing(10)
        render_bar.setVerticalSpacing(8)

        # Row 1: Scene class detection
        render_bar.addWidget(QLabel("🎬 Scene Class:"), 0, 0)
        self.scene_class_input = QLineEdit()
        self.scene_class_input.setPlaceholderText("Enter or auto-detect scene class name")
        self.scene_class_input.setObjectName("sceneInput")
        render_bar.addWidget(self.scene_class_input, 0, 1)
        
        detect_btn = QPushButton("🔍 Auto-Detect")
        detect_btn.setToolTip("Detect scene class from current file")
        detect_btn.setObjectName("detectBtn")
        detect_btn.clicked.connect(self.detect_scene_class)
        render_bar.addWidget(detect_btn, 0, 2)

        # Row 2: Quality and output type
        render_bar.addWidget(QLabel("⚙️ Quality:"), 1, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["📱 Low (480p)", "💻 High (1080p)", "🎥 4K (2160p)", "🖼️ Custom"])
        self.quality_combo.setObjectName("qualityCombo")
        render_bar.addWidget(self.quality_combo, 1, 1)

        render_bar.addWidget(QLabel("📤 Output:"), 1, 2)
        self.output_type_combo = QComboBox()
        self.output_type_combo.addItems(["🎬 MP4 Video", "🖼️ PNG Image", "📐 SVG Vector"])
        self.output_type_combo.setObjectName("outputCombo")
        render_bar.addWidget(self.output_type_combo, 1, 3)

        # Row 3: Action buttons
        action_buttons_layout = QHBoxLayout()
        
        self.render_btn = QPushButton("▶️ Render Animation")
        self.render_btn.setObjectName("renderBtn")
        self.render_btn.clicked.connect(self.render_scene)
        self.render_btn.setMinimumHeight(40)

        self.stop_render_btn = QPushButton("⏹️ Stop Render")
        self.stop_render_btn.setObjectName("stopBtn")
        self.stop_render_btn.clicked.connect(self.stop_rendering)
        self.stop_render_btn.setMinimumHeight(40)
        
        self.open_output_btn = QPushButton("🎬 Open Output")
        self.open_output_btn.setObjectName("openOutputBtn")
        self.open_output_btn.clicked.connect(self.open_last_output)
        self.open_output_btn.setEnabled(False)
        self.open_output_btn.setMinimumHeight(40)

        self.open_output_folder_btn = QPushButton("📁 Open Output Folder")
        self.open_output_folder_btn.setObjectName("openOutputFolderBtn")
        self.open_output_folder_btn.clicked.connect(self.open_output_folder)
        self.open_output_folder_btn.setEnabled(False)
        self.open_output_folder_btn.setMinimumHeight(40)
        
        preview_btn = QPushButton("👁️ Preview Code")
        preview_btn.setObjectName("previewBtn")
        preview_btn.clicked.connect(self.preview_code)
        preview_btn.setMinimumHeight(40)

        action_buttons_layout.addWidget(self.render_btn)
        action_buttons_layout.addWidget(self.open_output_btn)
        action_buttons_layout.addWidget(self.open_output_folder_btn)
        action_buttons_layout.addWidget(self.preview_btn)
        action_buttons_layout.addWidget(self.stop_render_btn)
        
        render_bar.addLayout(action_buttons_layout, 2, 0, 1, 4)

        layout.addWidget(self.render_controls_widget)

        # Enhanced progress bar with animation counter and status
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QHBoxLayout(progress_frame)
        progress_layout.setContentsMargins(15, 10, 15, 10)
        
        self.status_indicator = QLabel("⚪ Ready")
        self.status_indicator.setObjectName("statusIndicator")
        self.status_indicator.setMinimumWidth(120)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setMinimumHeight(25)
        
        self.animation_counter = QLabel("🎞️ Animations: 0/0")
        self.animation_counter.setObjectName("animationCounter")
        self.animation_counter.setMinimumWidth(150)
        self.animation_counter.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        progress_layout.addWidget(self.status_indicator)
        progress_layout.addWidget(self.progress_bar, 1)
        progress_layout.addWidget(self.animation_counter)
        layout.addWidget(progress_frame)

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

    def apply_modern_stylesheet(self):
        """Apply a modern, professional dark theme stylesheet"""
        self.setStyleSheet("""
            /* Main window and panels */
            QWidget#ManimGUI {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 10pt;
            }
            
            /* Top bar with gradient effect */
            QFrame#topBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #313244, stop:0.5 #45475a, stop:1 #313244);
                border-bottom: 2px solid #89b4fa;
            }
            
            /* Project label styling */
            QLabel#projectLabel {
                color: #cdd6f4;
                font-size: 12pt;
                font-weight: bold;
                padding: 5px;
            }
            
            /* Panel headers */
            QLabel#panelHeader {
                color: #89b4fa;
                font-size: 9pt;
                font-weight: bold;
                padding: 8px;
                background-color: #313244;
                border-radius: 4px;
                margin: 5px;
            }
            
            /* Explorer panel */
            QFrame#explorerPanel {
                background-color: #181825;
                border-right: 1px solid #313244;
            }
            
            /* Editor panel */
            QFrame#editorPanel {
                background-color: #1e1e2e;
            }
            
            /* Log panel */
            QFrame#logPanel {
                background-color: #11111b;
                border-top: 2px solid #313244;
            }
            
            /* Render controls */
            QFrame#renderControls {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #313244, stop:1 #45475a);
                border-top: 1px solid #585b70;
            }
            
            /* Progress frame */
            QFrame#progressFrame {
                background-color: #181825;
                border-top: 1px solid #89b4fa;
            }
            
            /* Splitter handles */
            QSplitter::handle {
                background: #45475a;
            }
            QSplitter::handle:horizontal {
                width: 3px;
            }
            QSplitter::handle:vertical {
                height: 3px;
            }
            QSplitter::handle:hover {
                background: #89b4fa;
            }
            
            /* Buttons - Primary */
            QPushButton#primaryBtn {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
            }
            QPushButton#primaryBtn:hover {
                background-color: #b4befe;
            }
            QPushButton#primaryBtn:pressed {
                background-color: #7287fd;
            }
            
            /* Buttons - Action */
            QPushButton#actionBtn {
                background-color: #45475a;
                color: #cdd6f4;
                padding: 8px 14px;
                border: 1px solid #585b70;
                border-radius: 6px;
            }
            QPushButton#actionBtn:hover {
                background-color: #585b70;
                border-color: #89b4fa;
            }
            
            /* Icon buttons */
            QToolButton#iconBtn {
                background-color: transparent;
                color: #cdd6f4;
                font-size: 16px;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QToolButton#iconBtn:hover {
                background-color: #45475a;
            }
            
            /* Render button */
            QPushButton#renderBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #a6e3a1, stop:1 #94e2d5);
                color: #1e1e2e;
                font-weight: bold;
                font-size: 11pt;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
            }
            QPushButton#renderBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #94e2d5, stop:1 #a6e3a1);
            }
            QPushButton#renderBtn:pressed {
                background: #74c7ec;
            }
            
            /* Stop button */
            QPushButton#stopBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f38ba8, stop:1 #eba0ac);
                color: #1e1e2e;
                font-weight: bold;
                font-size: 11pt;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
            }
            QPushButton#stopBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #eba0ac, stop:1 #f38ba8);
            }
            
            /* Open output button */
            QPushButton#openOutputBtn {
                background-color: #f9e2af;
                color: #1e1e2e;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
            }
            QPushButton#openOutputBtn:hover {
                background-color: #fab387;
            }
            QPushButton#openOutputBtn:disabled {
                background-color: #45475a;
                color: #6c7086;
            }

            QPushButton#openOutputFolderBtn {
                background-color: #74c7ec;
                color: #1e1e2e;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
            }
            QPushButton#openOutputFolderBtn:hover {
                background-color: #89dceb;
            }
            QPushButton#openOutputFolderBtn:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            
            /* Preview button */
            QPushButton#previewBtn {
                background-color: #cba6f7;
                color: #1e1e2e;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
            }
            QPushButton#previewBtn:hover {
                background-color: #b4befe;
            }
            
            /* Detect button */
            QPushButton#detectBtn {
                background-color: #94e2d5;
                color: #1e1e2e;
                font-weight: bold;
                padding: 8px 14px;
                border: none;
                border-radius: 6px;
            }
            QPushButton#detectBtn:hover {
                background-color: #89dceb;
            }
            
            /* Generic buttons */
            QPushButton, QToolButton {
                background-color: #45475a;
                color: #cdd6f4;
                padding: 6px 12px;
                border: 1px solid #585b70;
                border-radius: 4px;
            }
            QPushButton:hover, QToolButton:hover {
                background-color: #585b70;
                border-color: #89b4fa;
            }
            QPushButton:pressed, QToolButton:pressed {
                background-color: #6c7086;
            }
            
            /* Log buttons */
            QToolButton#logBtn {
                background-color: #313244;
                color: #cdd6f4;
                padding: 5px 10px;
                border: 1px solid #45475a;
                border-radius: 4px;
                font-size: 9pt;
            }
            QToolButton#logBtn:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }

            QComboBox#logLevelCombo {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #585b70;
                border-radius: 6px;
                padding: 4px 8px;
                min-height: 24px;
            }
            QCheckBox#logCheck {
                color: #a6adc8;
                spacing: 6px;
                font-size: 9pt;
            }
            
            /* Input fields */
            QLineEdit#sceneInput {
                background-color: #313244;
                color: #cdd6f4;
                border: 2px solid #45475a;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10pt;
            }
            QLineEdit#sceneInput:focus {
                border-color: #89b4fa;
            }
            QLineEdit#sceneInput::placeholder {
                color: #6c7086;
            }
            
            /* Text editor and outputs */
            QTextEdit#outputLog {
                background-color: #11111b;
                color: #a6adc8;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: none;
                padding: 10px;
            }
            
            QLineEdit, QTextEdit, QTreeView, QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #89b4fa;
            }
            
            /* ComboBoxes */
            QComboBox#qualityCombo, QComboBox#outputCombo {
                background-color: #45475a;
                color: #cdd6f4;
                border: 1px solid #585b70;
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 25px;
            }
            QComboBox#qualityCombo:focus, QComboBox#outputCombo:focus {
                border-color: #89b4fa;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #89b4fa;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                selection-background-color: #45475a;
            }
            
            /* TabWidget */
            QTabWidget#codeTabs::pane {
                border: none;
                background-color: #1e1e2e;
            }
            QTabBar::tab {
                background-color: #313244;
                color: #a6adc8;
                border: 1px solid #45475a;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 120px;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e2e;
                color: #89b4fa;
                border-color: #89b4fa;
                border-bottom: 2px solid #1e1e2e;
            }
            QTabBar::tab:!selected:hover {
                background-color: #45475a;
                color: #cdd6f4;
            }
            QTabBar::tab:first:selected {
                margin-left: 0;
            }
            
            /* ProgressBar */
            QProgressBar#progressBar {
                border: 2px solid #45475a;
                border-radius: 12px;
                text-align: center;
                background-color: #313244;
                color: #cdd6f4;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar#progressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #a6e3a1, stop:0.5 #94e2d5, stop:1 #89dceb);
                border-radius: 10px;
            }
            
            /* Status indicator */
            QLabel#statusIndicator {
                color: #a6adc8;
                font-weight: bold;
                padding: 5px;
                background-color: #313244;
                border-radius: 4px;
            }
            
            /* Animation counter */
            QLabel#animationCounter {
                color: #f9e2af;
                font-weight: bold;
                font-size: 10pt;
                padding: 5px;
            }
            
            /* TreeView (File explorer) */
            QTreeView {
                background-color: #181825;
                color: #cdd6f4;
                border: none;
                padding: 5px;
                outline: none;
            }
            QTreeView::item {
                padding: 5px;
                border-radius: 3px;
            }
            QTreeView::item:hover {
                background-color: #313244;
            }
            QTreeView::item:selected {
                background-color: #45475a;
                color: #89b4fa;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: none;
                image: none;
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none;
                image: none;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background-color: #1e1e2e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #45475a;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #585b70;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #1e1e2e;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #45475a;
                border-radius: 5px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #585b70;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

    def create_default_project(self):
        """Create a default project folder and file if none exists"""
        default_path = os.path.join(os.path.expanduser("~"), "ManimProjects")
        if not os.path.exists(default_path):
            os.makedirs(default_path)
        
        self.project_path = default_path
        self.project_label.setText(f"📁 {os.path.basename(default_path)}")
        self.file_tree.setRootIndex(self.file_model.setRootPath(default_path))
        
        default_file = os.path.join(default_path, "default_scene.py")
        if not os.path.exists(default_file):
            with open(default_file, 'w') as f:
                f.write(self.default_scene_template())
            self.open_scene_file(default_file)

    def init_menu_bar(self):
        """Initialize the menu bar with File, Edit, View, Tools, and Help menus"""
        menubar = QMenuBar(self)
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1e1e2e;
                color: #cdd6f4;
                padding: 5px;
                border-bottom: 1px solid #313244;
            }
            QMenuBar::item:selected {
                background-color: #45475a;
                border-radius: 4px;
            }
            QMenu {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #45475a;
                color: #89b4fa;
            }
            QMenu::separator {
                height: 1px;
                background-color: #45475a;
                margin: 5px 10px;
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu("📁 File")
        
        new_action = QAction("➕ New Scene", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.create_new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("📂 Open Project", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.select_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("💾 Save Current File", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_current_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Exit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("✏️ Edit")
        
        undo_action = QAction("↩️ Undo", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.undo_edit)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("↪️ Redo", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.redo_edit)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("✂️ Cut", self)
        cut_action.setShortcut(QKeySequence("Ctrl+X"))
        cut_action.triggered.connect(self.cut_text)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("📋 Copy", self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_action.triggered.connect(self.copy_text)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("📌 Paste", self)
        paste_action.setShortcut(QKeySequence("Ctrl+V"))
        paste_action.triggered.connect(self.paste_text)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        select_all_action = QAction("✅ Select All", self)
        select_all_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_action.triggered.connect(self.select_all_text)
        edit_menu.addAction(select_all_action)
        
        # View menu
        view_menu = menubar.addMenu("👁️ View")
        
        fullscreen_action = QAction("⛶ Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        view_menu.addSeparator()
        
        zoom_in_action = QAction("🔍 Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("🔎 Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("🔧 Tools")
        
        snippets_action = QAction("📝 Code Snippets", self)
        snippets_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        snippets_action.triggered.connect(self.show_snippets_panel)
        tools_menu.addAction(snippets_action)
        
        tools_menu.addSeparator()
        
        detect_action = QAction("🔍 Detect Scene Class", self)
        detect_action.setShortcut(QKeySequence("Ctrl+D"))
        detect_action.triggered.connect(self.detect_scene_class)
        tools_menu.addAction(detect_action)
        
        count_action = QAction("📊 Count Animations", self)
        count_action.triggered.connect(self.count_animations)
        tools_menu.addAction(count_action)
        
        tools_menu.addSeparator()
        
        render_action = QAction("▶️ Render", self)
        render_action.setShortcut(QKeySequence("F5"))
        render_action.triggered.connect(self.render_scene)
        tools_menu.addAction(render_action)
        
        stop_action = QAction("⏹️ Stop Render", self)
        stop_action.setShortcut(QKeySequence("Ctrl+Break"))
        stop_action.triggered.connect(self.stop_rendering)
        tools_menu.addAction(stop_action)
        
        # Help menu
        help_menu = menubar.addMenu("❓ Help")
        
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        layout = self.layout()
        layout.insertWidget(0, menubar)

    def init_toolbar(self):
        """Initialize a quick access toolbar"""
        toolbar = QToolBar(self)
        toolbar.setObjectName("quickToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setStyleSheet("""
            QToolBar#quickToolbar {
                background-color: #313244;
                border-bottom: 1px solid #45475a;
                padding: 5px;
                spacing: 5px;
            }
            QToolButton {
                background-color: transparent;
                color: #cdd6f4;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QToolButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
            QToolButton:pressed {
                background-color: #585b70;
            }
            QToolBar::separator {
                background-color: #45475a;
                width: 1px;
                margin: 5px;
            }
        """)
        
        # Add toolbar actions
        new_btn = toolbar.addAction("➕")
        new_btn.setToolTip("New Scene (Ctrl+N)")
        new_btn.triggered.connect(self.create_new_file)
        
        open_btn = toolbar.addAction("📂")
        open_btn.setToolTip("Open Project (Ctrl+O)")
        open_btn.triggered.connect(self.select_project)
        
        toolbar.addSeparator()
        
        save_btn = toolbar.addAction("💾")
        save_btn.setToolTip("Save (Ctrl+S)")
        save_btn.triggered.connect(self.save_current_file)
        
        toolbar.addSeparator()
        
        undo_btn = toolbar.addAction("↩️")
        undo_btn.setToolTip("Undo (Ctrl+Z)")
        undo_btn.triggered.connect(self.undo_edit)
        
        redo_btn = toolbar.addAction("↪️")
        redo_btn.setToolTip("Redo (Ctrl+Y)")
        redo_btn.triggered.connect(self.redo_edit)
        
        toolbar.addSeparator()
        
        render_btn = toolbar.addAction("▶️")
        render_btn.setToolTip("Render (F5)")
        render_btn.triggered.connect(self.render_scene)
        
        layout = self.layout()
        # Insert toolbar after menu bar (position 1)
        if layout.count() > 0:
            layout.insertWidget(1, toolbar)

    def load_snippets(self):
        """Load code snippets from settings or return defaults"""
        default_snippets = {
            "Circle Animation": """circle = Circle(color=BLUE)\nself.play(Create(circle))\nself.wait()""",
            "Square Animation": """square = Square(color=GREEN)\nself.play(Create(square))\nself.wait()""",
            "Text Animation": """text = Text("Hello World!", font_size=36)\nself.play(Write(text))\nself.wait()""",
            "Transform": """circle = Circle()\nsquare = Square()\nself.play(Create(circle))\nself.play(Transform(circle, square))\nself.wait()""",
            "Fade In/Out": """obj = Circle()\nself.play(FadeIn(obj))\nself.wait()\nself.play(FadeOut(obj))""",
            "Move To": """obj = Dot()\nself.play(obj.animate.move_to(ORIGIN))\nself.wait()""",
            "Rotate": """square = Square()\nself.play(Create(square))\nself.play(Rotate(square, angle=PI/2))\nself.wait()""",
            "Scale": """circle = Circle()\nself.play(Create(circle))\nself.play(circle.animate.scale(2))\nself.wait()""",
            "Color Change": """circle = Circle()\nself.play(Create(circle))\nself.play(circle.animate.set_color(RED))\nself.wait()""",
            "Group Objects": """circle = Circle()\nsquare = Square()\ngroup = VGroup(circle, square).arrange(RIGHT)\nself.play(Create(group))\nself.wait()""",
            "3D Axes Setup": """class ThreeDSceneDemo(ThreeDScene):\n    def construct(self):\n        axes = ThreeDAxes()\n        self.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)\n        self.play(Create(axes))\n        self.wait()""",
            "ValueTracker + Updater": """tracker = ValueTracker(0)\ndot = Dot()\ndot.add_updater(lambda d: d.move_to(RIGHT * tracker.get_value()))\nself.add(dot)\nself.play(tracker.animate.set_value(4), run_time=2)\nself.wait()""",
            "MathTex Equation": """eq = MathTex(r\"e^{i\\pi} + 1 = 0\")\nself.play(Write(eq))\nself.wait()""",
            "Graph Plot": """axes = Axes(x_range=[-3, 3], y_range=[-1, 9])\ncurve = axes.plot(lambda x: x**2, color=BLUE)\nself.play(Create(axes), Create(curve))\nself.wait()"""
        }
        
        settings = QSettings("ManimGUI", "Snippets")
        saved = settings.value("snippets")
        if saved:
            return json.loads(saved)
        return default_snippets

    def show_snippets_panel(self):
        """Show a dialog with available code snippets"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📝 Code Snippets")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QListWidget {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #45475a;
                color: #89b4fa;
            }
            QListWidget::item:hover {
                background-color: #585b70;
            }
            QTextEdit {
                background-color: #11111b;
                color: #a6adc8;
                font-family: 'Consolas', monospace;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # Snippet list
        list_label = QLabel("📋 Available Snippets:")
        list_label.setStyleSheet("font-weight: bold; color: #89b4fa;")
        layout.addWidget(list_label)
        
        snippet_list = QListWidget()
        for name in self.snippets.keys():
            item = QListWidgetItem(f"📝 {name}")
            snippet_list.addItem(item)
        snippet_list.currentRowChanged.connect(lambda idx: self.preview_snippet(snippet_list, preview_text, idx))
        layout.addWidget(snippet_list)
        
        # Preview area
        preview_label = QLabel("👁️ Preview:")
        preview_label.setStyleSheet("font-weight: bold; color: #89b4fa;")
        layout.addWidget(preview_label)
        
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setMaximumHeight(150)
        layout.addWidget(preview_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        insert_btn = QPushButton("📌 Insert at Cursor")
        insert_btn.clicked.connect(lambda: self.insert_snippet(snippet_list, dialog))
        btn_layout.addWidget(insert_btn)
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Select first item by default
        if snippet_list.count() > 0:
            snippet_list.setCurrentRow(0)
        
        dialog.exec()

    def preview_snippet(self, list_widget, preview_text, index):
        """Preview the selected snippet"""
        if index >= 0 and index < len(self.snippets):
            name = list_widget.item(index).text().replace("📝 ", "")
            code = self.snippets.get(name, "")
            preview_text.setPlainText(code)

    def insert_snippet(self, list_widget, dialog):
        """Insert the selected snippet at cursor position"""
        current_row = list_widget.currentRow()
        if current_row >= 0:
            name = list_widget.item(current_row).text().replace("📝 ", "")
            code = self.snippets.get(name, "")
            
            filepath, editor = self.get_current_file_path()
            if editor:
                cursor = editor.textCursor()
                cursor.insertText(code)
                self.append_to_log(f"📝 Inserted snippet: {name}", "info")
                dialog.close()
            else:
                QMessageBox.warning(self, "No File Open", "Please open a file first.")

    def export_logs(self):
        """Export render logs to a text file"""
        if not self.output_log.toPlainText().strip():
            QMessageBox.information(self, "No Logs", "There are no logs to export.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "", "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.output_log.toPlainText())
                self.append_to_log(f"💾 Logs exported to: {filename}", "info")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Could not export logs:\n{e}")

    def preview_code(self):
        """Show a syntax-highlighted preview of the current code"""
        filepath, editor = self.get_current_file_path()
        if not editor:
            QMessageBox.warning(self, "No File Open", "Please open a file first.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("👁️ Code Preview")
        dialog.setMinimumSize(700, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QTextEdit {
                background-color: #11111b;
                color: #a6adc8;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        preview_label = QLabel("📄 Code Preview:")
        preview_label.setStyleSheet("font-weight: bold; color: #89b4fa; font-size: 12pt;")
        layout.addWidget(preview_label)
        
        preview_editor = QTextEdit()
        preview_editor.setReadOnly(True)
        preview_editor.setPlainText(editor.toPlainText())
        PythonSyntaxHighlighter(preview_editor.document())
        layout.addWidget(preview_editor)
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec()

    def load_recent_projects(self):
        """Load recent projects from settings"""
        settings = QSettings("ManimGUI", "RecentProjects")
        self.recent_projects = settings.value("projects", [])
        if not isinstance(self.recent_projects, list):
            self.recent_projects = []

    def save_current_file(self):
        """Save the current file"""
        filepath, editor = self.get_current_file_path()
        if filepath and editor:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(editor.toPlainText())
                self.append_to_log(f"💾 Saved: {os.path.basename(filepath)}", "info")
            except Exception as e:
                QMessageBox.critical(self, "Save Failed", f"Could not save file:\n{e}")

    def undo_edit(self):
        """Undo last edit in current editor"""
        filepath, editor = self.get_current_file_path()
        if editor:
            editor.undo()

    def redo_edit(self):
        """Redo last undone edit in current editor"""
        filepath, editor = self.get_current_file_path()
        if editor:
            editor.redo()

    def cut_text(self):
        """Cut selected text"""
        filepath, editor = self.get_current_file_path()
        if editor:
            editor.cut()

    def copy_text(self):
        """Copy selected text"""
        filepath, editor = self.get_current_file_path()
        if editor:
            editor.copy()

    def paste_text(self):
        """Paste text from clipboard"""
        filepath, editor = self.get_current_file_path()
        if editor:
            editor.paste()

    def select_all_text(self):
        """Select all text in current editor"""
        filepath, editor = self.get_current_file_path()
        if editor:
            editor.selectAll()

    def zoom_in(self):
        """Zoom in the current editor"""
        filepath, editor = self.get_current_file_path()
        if editor:
            font = editor.font()
            font.setPointSize(font.pointSize() + 1)
            editor.setFont(font)

    def zoom_out(self):
        """Zoom out the current editor"""
        filepath, editor = self.get_current_file_path()
        if editor:
            font = editor.font()
            if font.pointSize() > 6:
                font.setPointSize(font.pointSize() - 1)
                editor.setFont(font)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Manim GUI Editor",
            "<h2>Manim GUI Editor - Professional</h2>"
            "<p>A modern, professional GUI for creating Manim animations.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Modern dark theme UI</li>"
            "<li>Syntax highlighting for Python/Manim</li>"
            "<li>Code snippets library</li>"
            "<li>Real-time render progress tracking</li>"
            "<li>File explorer integration</li>"
            "<li>Multiple quality presets</li>"
            "</ul>"
            "<p>Built with PyQt6</p>"
        )

    def update_from_github(self):
        """Update the local app by pulling the latest changes from git remote"""
        repo_dir = os.path.dirname(os.path.abspath(__file__))
        git_dir = os.path.join(repo_dir, ".git")

        if not os.path.isdir(git_dir):
            QMessageBox.warning(
                self,
                "Update Unavailable",
                "No git repository found in the app directory."
            )
            return

        self.append_to_log("🔄 Checking for updates from GitHub...", "info")
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=repo_dir,
            capture_output=True,
            text=True
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        details = "\n".join(part for part in [stdout, stderr] if part).strip()
        if details:
            self.append_to_log(details, "normal")

        if result.returncode == 0:
            self.append_to_log("✅ Update completed successfully.", "info")
            QMessageBox.information(
                self,
                "Update Complete",
                "The app was updated successfully.\nRestart the app to apply all changes."
            )
        else:
            self.append_to_log("❌ Update failed. Check logs for details.", "error")
            QMessageBox.critical(
                self,
                "Update Failed",
                f"Could not update from GitHub.\n\n{details or 'Unknown git error.'}"
            )

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

        quality_map = {
            "📱 Low (480p)": "-ql",
            "💻 High (1080p)": "-qh",
            "🎥 4K (2160p)": "-qk",
            "🖼️ Custom": "-qm"
        }
        quality = self.quality_combo.currentText()
        flag = quality_map.get(quality, "-qh")
        
        output_type = self.output_type_combo.currentText()
        if output_type == "🎬 MP4 Video":
            cmd = f"manim -p {flag} \"{filepath}\" {scene_class}"
        elif output_type == "🖼️ PNG Image":
            cmd = f"manim -s {flag} \"{filepath}\" {scene_class}"
        elif output_type == "📐 SVG Vector":
            cmd = f"manim -s --format=svg {flag} \"{filepath}\" {scene_class}"
        else:
            cmd = f"manim -p {flag} \"{filepath}\" {scene_class}"

        self.log_history.clear()
        self.output_log.clear()
        self.last_progress = 0
        self.completed_animations = 0
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        self.last_output_path = ""
        self.last_output_dir = ""
        self.open_output_btn.setEnabled(False)
        self.open_output_folder_btn.setEnabled(False)
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
                self.last_output_dir = os.path.dirname(self.last_output_path)
                self.append_to_log(f"🎥 Output available at: {self.last_output_path}", "info")

        if "INFO" in line: self.append_to_log(line, "info")
        elif "WARNING" in line: self.append_to_log(line, "warning")
        elif "ERROR" in line or "Exception" in line: self.append_to_log(line, "error")
        else: self.append_to_log(line, "normal")

    def append_to_log(self, text, msg_type):
        self.log_history.append((text, msg_type))
        self.refresh_log_display()

    def _log_type_allowed(self, msg_type):
        current_filter = self.log_level_combo.currentText() if hasattr(self, "log_level_combo") else "All Logs"
        if current_filter == "Info Only":
            return msg_type == "info"
        if current_filter == "Warnings+":
            return msg_type in {"warning", "error"}
        if current_filter == "Errors Only":
            return msg_type == "error"
        return True

    def refresh_log_display(self):
        if not hasattr(self, "output_log"):
            return
        self.output_log.clear()
        cursor = self.output_log.textCursor()
        for text, msg_type in self.log_history:
            if not self._log_type_allowed(msg_type):
                continue
            cursor.movePosition(QTextCursor.MoveOperation.End)
            format = QTextCharFormat()
            if msg_type == "error":
                format.setForeground(QColor("#ff4444"))
                format.setFontWeight(75)
            elif msg_type == "warning":
                format.setForeground(QColor("#ffbb33"))
            elif msg_type == "info":
                format.setForeground(QColor("#33b5e5"))
            else:
                format.setForeground(QColor("#f8f8f8"))

            cursor.setCharFormat(format)
            cursor.insertText(text + "\n")

        if self.autoscroll_checkbox.isChecked():
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
                self.open_output_folder_btn.setEnabled(True)
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

    def copy_selected_logs(self):
        selected = self.output_log.textCursor().selectedText()
        if selected.strip():
            QApplication.clipboard().setText(selected)
            self.append_to_log("✂️ Selected logs copied to clipboard", "info")
        else:
            self.append_to_log("⚠️ No log text selected to copy", "warning")

    def clear_logs(self):
        self.log_history.clear()
        self.output_log.clear()

    def open_output_folder(self):
        if self.last_output_dir and os.path.exists(self.last_output_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_output_dir))
        elif self.last_output_path and os.path.exists(os.path.dirname(self.last_output_path)):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(self.last_output_path)))
        else:
            QMessageBox.warning(self, "Folder Not Found", "No output folder is available yet. Render a scene first.")

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

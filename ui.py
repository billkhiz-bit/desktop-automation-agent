# modern_chat_widget.py
"""
Modern Chat Widget for Desktop Agent V2
Non-blocking UI with proper result display
"""

import sys
import requests
import json
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTextEdit, QPushButton, QLabel, QScrollArea, QFrame,
                            QSizeGrip, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QTextCursor

class AgentWorker(QThread):
    """Worker thread for non-blocking requests"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, backend_url, message):
        super().__init__()
        self.backend_url = backend_url
        self.message = message
    
    def run(self):
        try:
            response = requests.post(
                f"{self.backend_url}/agent",
                json={"task": self.message},
                timeout=120
            )
            
            if response.status_code == 200:
                self.finished.emit(response.json())
            else:
                self.error.emit(f"Server error: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.error.emit("Cannot connect to backend. Make sure it's running on port 5001.")
        except Exception as e:
            self.error.emit(str(e))

class ModernChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.backend_url = "http://localhost:5001"
        self.drag_position = QPoint()
        self.worker = None
        self.initUI()
        self.check_connection()
        self.setup_hotkey()
        
    def initUI(self):
        # Frameless window with dark theme
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container
        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 16px;
                border: 1px solid #3d3d3d;
            }
        """)
        
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Custom title bar
        title_bar = self.create_title_bar()
        container_layout.addWidget(title_bar)
        
        # Chat area
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(20, 10, 20, 20)
        chat_layout.setSpacing(15)
        
        # Messages scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #4d4d4d;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5d5d5d;
            }
        """)
        
        # Messages container
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.messages_widget)
        
        chat_layout.addWidget(self.scroll_area)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2d2d2d;
                border: none;
                border-radius: 5px;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 5px;
            }
        """)
        self.progress_bar.hide()
        chat_layout.addWidget(self.progress_bar)
        
        # Quick actions
        quick_actions = self.create_quick_actions()
        chat_layout.addWidget(quick_actions)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Type your command here...")
        self.input_field.setMaximumHeight(80)
        self.input_field.setFont(QFont("Segoe UI", 10))
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #252525;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                padding: 10px;
            }
            QTextEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        self.input_field.installEventFilter(self)
        
        self.send_button = QPushButton("Send")
        self.send_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.send_button.setFixedSize(100, 50)
        self.send_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }
            QPushButton:pressed {
                background: #1e40af;
            }
            QPushButton:disabled {
                background: #374151;
                color: #6b7280;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        
        chat_layout.addLayout(input_layout)
        
        # Status bar
        self.status_label = QLabel("● Ready")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setStyleSheet("color: #10b981; padding: 5px;")
        chat_layout.addWidget(self.status_label)
        
        container_layout.addLayout(chat_layout)
        
        # Add resize grip
        self.size_grip = QSizeGrip(main_container)
        self.size_grip.setStyleSheet("QSizeGrip { background-color: transparent; }")
        container_layout.addWidget(self.size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        
        # Set main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_container)
        self.setLayout(main_layout)
        
        # Window settings
        self.setGeometry(100, 100, 600, 700)
        self.setMinimumSize(400, 500)
        self.setWindowTitle('Desktop Agent V2')
        
        # Welcome message
        self.add_agent_message("👋 Desktop Agent ready! I have 48 tools.\n\nTry: 'Take a screenshot' or 'Create a budget for £500'")
        
    def create_title_bar(self):
        title_bar = QFrame()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom: 1px solid #3d3d3d;
            }
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(20, 0, 15, 0)
        
        title_label = QLabel("🤖 Desktop Agent V2")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Segoe UI", 14))
        self.status_indicator.setStyleSheet("color: #6b7280;")
        layout.addWidget(self.status_indicator)
        
        min_btn = QPushButton("−")
        min_btn.setFixedSize(30, 30)
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9ca3af;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #374151;
                border-radius: 5px;
            }
        """)
        min_btn.clicked.connect(self.showMinimized)
        layout.addWidget(min_btn)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9ca3af;
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: white;
                border-radius: 5px;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move
        
        return title_bar
    
    def title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
    
    def title_bar_mouse_move(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
    
    def create_quick_actions(self):
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: transparent; }")
        
        layout = QHBoxLayout(container)
        layout.setSpacing(8)
        
        actions = [
            ("📊 Budget", "Create a budget for £500 with rent 300, food 200"),
            ("📧 Emails", "Read my last 5 emails"),
            ("📁 Files", "List files on desktop"),
            ("📸 Screenshot", "Take a screenshot"),
        ]
        
        for label, command in actions:
            btn = QPushButton(label)
            btn.setFont(QFont("Segoe UI", 8))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #374151;
                    color: #d1d5db;
                    border: 1px solid #4b5563;
                    border-radius: 8px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #4b5563;
                    border-color: #6b7280;
                }
            """)
            btn.clicked.connect(lambda checked, cmd=command: self.quick_action(cmd))
            layout.addWidget(btn)
        
        return container
    
    def quick_action(self, command):
        self.input_field.setText(command)
        self.send_message()
    
    def add_user_message(self, text):
        bubble = QFrame()
        bubble.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border-radius: 14px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(12, 10, 12, 10)
        
        message_label = QLabel(text)
        message_label.setFont(QFont("Segoe UI", 10))
        message_label.setStyleSheet("color: white;")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(message_label)
        
        timestamp = QLabel(datetime.now().strftime("%H:%M"))
        timestamp.setFont(QFont("Segoe UI", 8))
        timestamp.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        timestamp.setAlignment(Qt.AlignRight)
        layout.addWidget(timestamp)
        
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(50, 0, 0, 0)
        container_layout.addWidget(bubble)
        
        self.messages_layout.addWidget(container)
        self.scroll_to_bottom()
    
    def add_agent_message(self, text):
        bubble = QFrame()
        bubble.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-radius: 14px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(12, 10, 12, 10)
        
        message_label = QLabel(text)
        message_label.setFont(QFont("Segoe UI", 10))
        message_label.setStyleSheet("color: #e5e7eb;")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        message_label.setOpenExternalLinks(True)
        layout.addWidget(message_label)
        
        timestamp = QLabel(datetime.now().strftime("%H:%M"))
        timestamp.setFont(QFont("Segoe UI", 8))
        timestamp.setStyleSheet("color: #6b7280;")
        layout.addWidget(timestamp)
        
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 50, 0)
        container_layout.addWidget(bubble)
        
        self.messages_layout.addWidget(container)
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
    
    def send_message(self):
        message = self.input_field.toPlainText().strip()
        if not message:
            return
        
        self.add_user_message(message)
        self.input_field.clear()
        self.set_status("Processing...", "yellow")
        self.send_button.setEnabled(False)
        self.progress_bar.show()
        
        # Start worker thread
        self.worker = AgentWorker(self.backend_url, message)
        self.worker.finished.connect(self.on_response_received)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_response_received(self, data):
        self.progress_bar.hide()
        self.send_button.setEnabled(True)
        
        # Build detailed response
        response_parts = []
        
        if data.get('success'):
            # Parse log for actual results
            log = data.get('log', [])
            
            for entry in log:
                # Screen info
                if 'screen_width' in entry or 'mouse_' in entry:
                    response_parts.append(entry.strip())
                # Files found
                elif 'Found' in entry and ('files' in entry or 'items' in entry):
                    response_parts.append(entry.strip())
                # File/item listings
                elif entry.strip().startswith('- '):
                    response_parts.append(entry.strip())
                # Credentials
                elif 'Stored credential' in entry or 'value:' in entry:
                    response_parts.append(entry.strip())
                # Screenshots
                elif 'Screenshot saved' in entry or 'saved to' in entry:
                    response_parts.append("📸 " + entry.strip())
                # Budget creation
                elif 'Created budget' in entry or 'categories' in entry:
                    response_parts.append("📊 " + entry.strip())
                # Emails
                elif 'Found' in entry and 'emails' in entry:
                    response_parts.append(entry.strip())
                # Application opened
                elif 'Opened' in entry:
                    response_parts.append("✅ " + entry.strip())
                # Step completion messages
                elif entry.strip().startswith('✓'):
                    response_parts.append(entry.strip())
            
            if response_parts:
                response_text = "\n".join(response_parts)
                self.add_agent_message(response_text)
            else:
                self.add_agent_message("✅ Task completed successfully")
            
            self.set_status("Ready", "green")
        else:
            error_msg = data.get('error', 'Unknown error')
            self.add_agent_message(f"❌ Error: {error_msg}")
            self.set_status("Error", "red")
    
    def on_error(self, error_msg):
        self.progress_bar.hide()
        self.send_button.setEnabled(True)
        self.add_agent_message(f"❌ {error_msg}")
        self.set_status("Error", "red")
    
    def set_status(self, text, color):
        colors = {
            "green": "#10b981",
            "yellow": "#f59e0b",
            "red": "#ef4444",
            "gray": "#6b7280"
        }
        self.status_label.setText(f"● {text}")
        self.status_label.setStyleSheet(f"color: {colors.get(color, '#6b7280')}; padding: 5px;")
        self.status_indicator.setStyleSheet(f"color: {colors.get(color, '#6b7280')};")
    
    def check_connection(self):
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=2)
            if response.status_code == 200:
                self.set_status("Connected", "green")
            else:
                self.set_status("Backend error", "red")
        except:
            self.set_status("Disconnected", "gray")
    
    def setup_hotkey(self):
        try:
            import keyboard
            keyboard.add_hotkey('ctrl+shift+a', self.toggle_window)
            print("✓ Hotkey: CTRL+SHIFT+A")
        except:
            print("✗ Hotkey setup failed")
    
    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
    
    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

if __name__ == '__main__':
    print("="*60)
    print("🤖 DESKTOP AGENT V2 - MODERN UI")
    print("="*60)
    print("✓ Non-blocking execution")
    print("✓ Hotkey: CTRL+SHIFT+A")
    print("="*60)
    
    app = QApplication(sys.argv)
    window = ModernChatWidget()
    window.show()
    sys.exit(app.exec_())
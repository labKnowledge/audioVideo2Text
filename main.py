
import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, 
                             QFileDialog, QTextEdit, QProgressBar, QHBoxLayout, QMainWindow, 
                            QStackedWidget, QStyle, QStyleFactory)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QRectF
from PyQt6.QtGui import QPainter, QIcon, QTextDocument, QPalette, QColor, QAction, QBrush, QPen, QFont
import moviepy.editor as mp
import ssl
import whisper
import time
import re

# Existing TranscriptionThread class remains unchanged

class TranscriptionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def format_text_to_paragraphs(self, text):
        # Remove any existing line breaks and extra spaces
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Split the text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        paragraphs = []
        current_paragraph = []
        
        for sentence in sentences:
            current_paragraph.append(sentence)
            
            # Check if we should start a new paragraph
            if len(current_paragraph) >= 3 or len(' '.join(current_paragraph)) > 250:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        # Add any remaining sentences as the last paragraph
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # Join paragraphs with double line breaks for clear separation
        formatted_text = '\n\n'.join(paragraphs)
        
        return formatted_text
    

    def run(self):
        try:
            self.progress.emit(0, "Preparing file for transcription...")
            
            # Check if the file is a video or audio
            file_extension = os.path.splitext(self.file_path)[1].lower()
            audio_path = self.file_path
            
            if file_extension in ['.mp4', '.avi', '.mov']:
                self.progress.emit(10, "Converting video to audio...")
                # Convert video to audio
                video_clip = mp.VideoFileClip(self.file_path)
                audio = video_clip.audio
                audio_path = os.path.splitext(self.file_path)[0] + f"_{time.time()}_.wav"
                audio.write_audiofile(audio_path, logger=None)
                self.progress.emit(30, "Audio extraction complete.")
            elif file_extension not in ['.mp3', '.wav', '.ogg', '.flac']:
                raise ValueError("Unsupported file format")

            self.progress.emit(40, "Loading transcription model...")
            ssl._create_default_https_context = ssl._create_unverified_context
            
            # Check if model is already downloaded
            model_path = os.path.expanduser("~/whisper_models")
            os.makedirs(model_path, exist_ok=True)
            model = whisper.load_model("base", download_root=model_path)

            self.progress.emit(60, "Transcribing audio...")
            result = model.transcribe(audio_path)
            transcript = self.format_text_to_paragraphs(result["text"])

            self.progress.emit(90, "Cleaning up...")
            # Clean up temporary audio file if it was created from video
            if audio_path != self.file_path:
                os.remove(audio_path)

            self.progress.emit(100, "Transcription complete!")
            self.finished.emit(transcript)
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)


class CircularProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.value = 0

    def setValue(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        width = self.width() - 1
        height = self.height() - 1
        margin = 10
        value = int(self.value * 360 / 100)  # Convert to integer

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(width / 2, height / 2)
        painter.scale(width / 200.0, height / 200.0)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(33, 150, 243)))

        painter.drawPie(QRectF(-90, -90, 180, 180), 90 * 16, -value * 16)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(-60, -60, 120, 120)

        painter.setPen(QPen(QColor(33, 150, 243)))
        painter.setFont(QFont('Arial', 30))
        painter.drawText(QRectF(-50, -50, 100, 100), Qt.AlignmentFlag.AlignCenter, f"{int(self.value)}%")




class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Modern Audio/Video Transcription App")
        self.setGeometry(100, 100, 1000, 700)

        # Create a central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create a stacked widget for different "pages"
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create and add the home page
        home_page = self.create_home_page()
        self.stacked_widget.addWidget(home_page)

        # Create and add the transcription page
        transcription_page = self.create_transcription_page()
        self.stacked_widget.addWidget(transcription_page)

        # Set up the menu bar
        self.create_menu_bar()

        # Set the initial theme
        self.set_theme("Light")

    def create_home_page(self):
        home_widget = QWidget()
        layout = QVBoxLayout(home_widget)

        welcome_label = QLabel("Welcome to the Audio/Video Transcription App")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("font-size: 24px; margin: 20px;")
        layout.addWidget(welcome_label)

        start_button = ModernButton("Start New Transcription")
        start_button.clicked.connect(self.start_transcription)
        layout.addWidget(start_button, alignment=Qt.AlignmentFlag.AlignCenter)

        return home_widget

    def create_transcription_page(self):
        transcription_widget = QWidget()
        layout = QVBoxLayout(transcription_widget)

        self.file_label = QLabel('Select an audio or video file to transcribe')
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.file_label)

        select_button = ModernButton('Select File')
        select_button.clicked.connect(self.selectFile)
        layout.addWidget(select_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = CircularProgressBar()
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.text_edit)

        return transcription_widget

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        new_action = QAction(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)), "&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)), "&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)), "&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)), "&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Theme menu
        theme_menu = menu_bar.addMenu("&Theme")
        
        light_theme_action = QAction("&Light", self)
        light_theme_action.triggered.connect(lambda: self.set_theme("Light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("&Dark", self)
        dark_theme_action.triggered.connect(lambda: self.set_theme("Dark"))
        theme_menu.addAction(dark_theme_action)

    def set_theme(self, theme):
        if theme == "Light":
            QApplication.setStyle(QStyleFactory.create("Fusion"))
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(230, 230, 230))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(76, 163, 224))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        else:  # Dark theme
            QApplication.setStyle(QStyleFactory.create("Fusion"))
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

        QApplication.setPalette(palette)

    def start_transcription(self):
        self.stacked_widget.setCurrentIndex(1)  # Switch to transcription page

    def selectFile(self):
            fileName, _ = QFileDialog.getOpenFileName(
                self,
                "Select Audio or Video File",
                "",
                "Audio/Video Files (*.mp3 *.wav *.ogg *.flac *.mp4 *.avi *.mov);;All Files (*)"
            )
            if fileName:
                self.file_label.setText(f"Processing: {os.path.basename(fileName)}")
                self.transcriptionThread = TranscriptionThread(fileName)
                self.transcriptionThread.finished.connect(self.updateTranscript)
                self.transcriptionThread.error.connect(self.showError)
                self.transcriptionThread.progress.connect(self.updateProgress)
                self.transcriptionThread.start()

    def updateTranscript(self, transcript):
        self.text_edit.setHtml(transcript)
        self.file_label.setText("Transcription complete")

    def showError(self, error_message):
        self.text_edit.setPlainText(error_message)
        self.file_label.setText("Error occurred")

    def updateProgress(self, value, message):
        self.progress_bar.setValue(value)
        self.file_label.setText(message)

    def new_file(self):
        self.text_edit.clear()
        self.stacked_widget.setCurrentIndex(0)  # Return to home page

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            with open(file_name, 'r') as file:
                self.text_edit.setText(file.read())
            self.stacked_widget.setCurrentIndex(1)  # Switch to transcription page

    def save_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            with open(file_name, 'w') as file:
                file.write(self.text_edit.toPlainText())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TextEditor()
    ex.show()
    sys.exit(app.exec())

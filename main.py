import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QFileDialog, QTextEdit, QProgressBar, QHBoxLayout, QMainWindow, QAction
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QTextDocument
import moviepy.editor as mp
import ssl
import whisper
import urllib
import time
import re
# Specify NumPy version
import numpy
if numpy.__version__.startswith('2.'):
    print("Warning: NumPy 2.x detected. Some modules may not be compatible.")
    print("Consider downgrading to NumPy 1.x or upgrading affected modules.")

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

class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize the main window
        self.setWindowTitle("Audio/Video Transcription App")
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add transcription-specific widgets
        self.label = QLabel('Select an audio or video file to transcribe')
        layout.addWidget(self.label)

        button_layout = QHBoxLayout()
        self.select_btn = QPushButton('Select File')
        self.select_btn.clicked.connect(self.selectFile)
        button_layout.addWidget(self.select_btn)

        layout.addLayout(button_layout)

        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(100)
        layout.addWidget(self.progressBar)

        # Create a QTextEdit widget
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        # Create a menu bar
        self.menu_bar = self.menuBar()

        # Create File menu
        file_menu = self.menu_bar.addMenu("&File")

        # Create actions
        new_action = QAction(QIcon(None), "&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        
        open_action = QAction(QIcon(None), "&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        
        save_action = QAction(QIcon(None), "&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        
        exit_action = QAction(QIcon(None), "&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Add actions to File menu
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

    def new_file(self):
        # Clear the text edit area
        self.text_edit.clear()
        

    def open_file(self):
        # Open a file dialog and read the selected file
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            with open(file_name, 'r') as file:
                self.text_edit.setText(file.read())

    def save_file(self):
        # Open a file dialog and save the file
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            with open(file_name, 'w') as file:
                file.write(self.text_edit.toPlainText())

    def selectFile(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Audio or Video File", "", 
                                                  "Audio/Video Files (*.mp3 *.wav *.ogg *.flac *.mp4 *.avi *.mov);;All Files (*)", 
                                                  options=options)
        if fileName:
            self.label.setText(f"Processing: {os.path.basename(fileName)}")
            self.transcriptionThread = TranscriptionThread(fileName)
            self.transcriptionThread.finished.connect(self.updateTranscript)
            self.transcriptionThread.error.connect(self.showError)
            self.transcriptionThread.progress.connect(self.updateProgress)
            self.transcriptionThread.start()

    def updateTranscript(self, transcript):
        self.text_edit.setHtml(transcript)  # Use setHtml to preserve any formatting
        self.label.setText("Transcription complete")

    def showError(self, error_message):
        self.text_edit.setPlainText(error_message)
        self.label.setText("Error occurred")

    def updateProgress(self, value, message):
        self.progressBar.setValue(value)
        self.label.setText(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TextEditor()
    ex.show()
    sys.exit(app.exec_())
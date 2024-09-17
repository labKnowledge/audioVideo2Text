# Audio/Video to Text Transcription App

This application provides a user-friendly GUI for transcribing audio and video files to text using OpenAI's Whisper model. It supports various audio and video formats and includes features like file selection, progress tracking, and text editing.

## Features

- Transcribe audio files (MP3, WAV, OGG, FLAC)
- Transcribe video files (MP4, AVI, MOV)
- User-friendly GUI with progress tracking
- Built-in text editor for reviewing and editing transcriptions
- Save transcriptions as text files

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7 or higher
- pip (Python package installer)
- FFmpeg (for video file processing)

## Installation

Follow these steps to set up the Audio/Video to Text Transcription App:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/audio-video2text.git
   cd audio-video2text
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application:

1. Ensure your virtual environment is activated.

2. Run the main script:
   ```
   python main.py
   ```

3. The application window will open. Click "Select File" to choose an audio or video file for transcription.

4. Wait for the transcription process to complete. You can monitor the progress in the application window.

5. Once transcription is finished, you can review and edit the text in the built-in editor.

6. Use the File menu to save your transcription or start a new file.

## Troubleshooting

- If you encounter issues with NumPy compatibility, try downgrading to NumPy 1.x:
  ```
  pip install numpy==1.21.0
  ```

- Ensure FFmpeg is properly installed and accessible in your system's PATH for video file processing.

## Contributing

Contributions to the Audio/Video to Text Transcription App are welcome. Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the transcription model
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- [MoviePy](https://zulko.github.io/moviepy/) for video processing

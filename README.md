# YouTube → Whisper Transcriber

A command-line tool that downloads audio from YouTube videos, transcribes it using OpenAI’s Whisper API, and saves a clean text transcript.

The tool is designed to be robust against:
- malformed or escaped YouTube URLs
- long videos that exceed Whisper’s file size limit
- environment and PATH issues (pyenv, conda, pip conflicts)

---

## Features

- Accepts multiple YouTube input formats:
  - Full URLs
  - watch?v=VIDEO_ID
  - Raw video IDs
  - Escaped or malformed strings (for example watch\?v\=...)
- Downloads best available audio and converts to MP3
- Automatically chunks long audio to bypass Whisper’s 25MB upload limit
- Cleans up temporary audio chunks after transcription
- Deterministic output structure:
  - MP3 files stored in downloads/
  - Transcripts stored in transcripts/

---

## Requirements

### System
- Python 3.11 or newer
- ffmpeg (required for audio processing)

### Python
- pipenv
- OpenAI API key

---

## Installation

### 1. Clone the repository

git clone <your-repo-url>
cd ytvideo-transcriber

---

### 2. Install system dependency

macOS:
brew install ffmpeg

Ubuntu / Debian:
sudo apt install ffmpeg

Verify:
ffmpeg -version

---

### 3. Set up Python environment with pipenv

pip install pipenv
pipenv install -r requirements.txt

This creates an isolated virtual environment with all required dependencies.

---

### 4. Configure OpenAI API key

Create a .env file in the project root:

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

Do not commit this file.

---

## Usage

You can run the tool either by entering the pipenv shell or by prefixing commands with pipenv run.

Option A: pipenv shell
pipenv shell
python transcriber.py watch?v=1BHOflzxPjI

Option B: one-shot execution
pipenv run python transcriber.py watch?v=1BHOflzxPjI

---

## Accepted Input Formats

All of the following are valid:

python transcriber.py 1BHOflzxPjI
python transcriber.py watch?v=1BHOflzxPjI
python transcriber.py watch?v=1BHOflzxPjI&t=10s
python transcriber.py https://www.youtube.com/watch?v=1BHOflzxPjI
python transcriber.py https://www.youtube.com/watch?\v\=1BHOflzxPjI&t=1s

Malformed or escaped input is normalized automatically.

---

## Output Structure

After a successful run:

project/
├── downloads/
│   └── video_title.mp3
├── transcripts/
│   └── video_title.txt

Temporary audio chunks are created during transcription and deleted automatically.

---

## How It Works (High Level)

1. Normalize user-provided YouTube input
2. Download best available audio via yt-dlp
3. Convert audio to MP3
4. Split MP3 into approximately 5-minute chunks
5. Send each chunk to OpenAI Whisper API
6. Concatenate transcript text
7. Save final transcript as .txt
8. Clean up temporary files

---

## Notes and Limitations

- Whisper API has a hard upload limit of about 25MB per request
- This is handled automatically via chunking
- Approximate cost is about 0.006 USD per minute of audio
- Only download and transcribe content you have the right to process

---

## Troubleshooting

yt-dlp errors:
Ensure yt-dlp is installed inside the pipenv environment:
pipenv run python -m yt_dlp --version

ffmpeg not found:
Ensure ffmpeg is installed and available on your system PATH.

---

## Development Notes

Recommended .gitignore entries:

.env
downloads/
transcripts/
audio_chunks/
__pycache__/

---

## License

MIT

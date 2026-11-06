# AI Air Writing System

A real-time computer vision project that lets you write in the air using your index finger in front of a webcam. The application tracks hand landmarks, draws smooth strokes over the live camera feed, and uses Tesseract OCR to attempt to convert the writing into text.

## Features

- Real-time webcam input using OpenCV
- Hand landmark tracking using MediaPipe
- Index finger gesture for air writing
- Open palm gesture to clear the writing
- Closed fist gesture to run text recognition
- Smooth, thick white drawing strokes over the live camera feed
- On-screen display for recognized text

## Technology Stack

- Python 3.11
- OpenCV
- MediaPipe
- NumPy
- Tesseract OCR
- Pytesseract

## Requirements

- Windows 10/11
- Python 3.11
- A working webcam
- Tesseract OCR installed separately

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/AI-Air-Writing-System.git
cd AI-Air-Writing-System
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create and activate a virtual environment (recommended)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install numpy==1.26.4 opencv-contrib-python==4.11.0.86 mediapipe==0.10.21 pytesseract
```

These versions are selected for compatibility with the legacy `mp.solutions.hands` API used by this project.

### 4. Install Tesseract OCR

Install the Windows version of Tesseract OCR from:

https://github.com/UB-Mannheim/tesseract/wiki

The Python file currently expects Tesseract at:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

If you installed it in a different location, update `TESSERACT_PATH` near the top of `air_writing_ready.py`.

### 5. Run the application

```powershell
python air_writing_ready.py
```

## Gesture Controls

| Gesture | Action |
| --- | --- |
| Index finger extended, other fingers folded | Write in the air |
| Open palm | Clear the writing canvas |
| Closed fist | Attempt OCR text recognition |
| `C` key | Clear the writing |
| `R` key | Run OCR recognition |
| `Esc` key | Exit the application |

## Usage Tips

- Keep your hand clearly visible to the webcam.
- Use good, even lighting.
- Write large, clear block letters.
- Keep letters separated and avoid writing too quickly.
- If the webcam does not open, close other applications using it or change `CAMERA_INDEX` in the Python file.

## OCR Limitations

Tesseract is a general-purpose OCR engine, not a handwriting-specific air-writing model. Recognition accuracy can vary, especially with connected letters, cursive writing, unusual letter shapes, or small strokes. This project attempts recognition; it cannot guarantee that every handwritten word will be recognized correctly.

## Project Structure

```text
AI-Air-Writing-System/
├── air_writing_ready.py
├── README.md
└── .gitignore
```

## License

Choose and add a license before allowing others to reuse or distribute this project.

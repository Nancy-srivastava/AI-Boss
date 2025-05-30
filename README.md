# AI BOSS – AI-Powered Interview Chatbot

AI BOSS is an AI-powered virtual interview assistant that analyzes your resume and conducts a personalized mock interview. Upload your resume and start your interview journey!

---

## Features

- Upload your resume (PDF or image)
- Resume parsing using Google Gemini AI
- Personalized technical interview with 25 questions
- Real-time chat interface
- Automated grading and feedback

---

## Getting Started

### 1. Clone the Repository

```sh
git clone https://github.com/yourusername/ai-boss.git
cd ai-boss
```

### 2. Create a Python Virtual Environment

```sh
python -m venv venv
```

#### Activate the virtual environment:

- **Windows:**
  ```sh
  venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```sh
  source venv/bin/activate
  ```

### 3. Install Dependencies

Make sure you have Poppler and fastapi installed and added to your PATH (required for PDF processing):

- **Poppler** Download from [Poppler for Windows](https://blog.alivate.com.au/poppler-windows/) and add the `bin` folder to your PATH.
- **FFMPEG** Download from [FFmpeg](https://github.com/FFmpeg/FFmpeg) and add the `bin` folder to your PATH.
- **MPV** Download from [MPV](https://mpv.io/installation/) and add the `bin` folder to your PATH.

- For Fastapi, you can install it using pip:
  ```sh
pip install fastapi
  ```


Then install Python dependencies:

```sh
pip install -r requirements.txt
```

### 4. Set Up API Keys

Create a `.env` file in the project root with the following content:

```
GOOGLE_API_KEY="your-google-api-key-here"
```

Replace `your-google-api-key-here` with your actual Google Gemini API key.

### 5. Run the Backend Server

```sh
python app.py
```

The API will be available at [http://localhost:5000](http://localhost:5000).

### 6. Frontend

Open `test/index.html` in your browser to use the web interface.

---

## File Structure

- `app.py` – FastAPI backend server
- `logic.py` – Interview logic and AI integration
- `requirements.txt` – Python dependencies
- `test/` – Frontend files (HTML, CSS, JS)
- `.env` – API keys (not committed to version control)

---

## Notes

- Make sure Poppler is installed and available in your system PATH for PDF resume parsing.
- The backend uses in-memory session storage. For production, use a persistent database or cache.
- The Google Gemini API key is required for AI features.

---

## License

MIT License

---

## Team

- Nancy Srivastava – Backend Developer
- Deepali Singh – Frontend Developer
- Afreen Siddiqui – Backend Developer
- 
=======

>>>>>>> f1a0c5c1eae0401ddecda91495c60395824242d0

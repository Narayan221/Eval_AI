# Automated Media Analysis Queue

A conceptual automated system that fetches media URLs from an external API, downloads them, and performs AI analysis (Human Activity Recognition + Audio Transcription).

## 🚀 How to Run

### 1. Configuration
Open `app/core/config.py` and set the following:
```python
# The API URL that returns your media links (JSON)
STARTUP_JOB_URL = "https://your-nextjs-app.com/api/get-session-data"

# How often to check/re-run (in minutes)
JOB_INTERVAL_MINUTES = 5
```

### 2. Start the Server
Run the application. It will automatically start the background polling loop.
```bash
uvicorn app.main:app --reload
```
Check the terminal console for analysis logs.

---

## 📂 Active System Files

These are the files currently powering the automation queue:

| File Path | Purpose |
| :--- | :--- |
| **`app/main.py`** | Entry point. Starts the background polling loop on boot. |
| **`app/core/config.py`** | Configuration (Target URL, Interval, API Keys). |
| **`app/services/analysis_job_service.py`** | The "Manager". Fetches API, downloads files, and orchestrates analysis. |
| **`app/services/activity_service.py`** | **Video AI**: Runs YOLOv8 for body pose and activity scoring. |
| **`app/services/transcription_service.py`** | **Audio AI**: Runs Faster-Whisper for text transcription. |
| **`app/routers/analysis.py`** | **Manual Trigger**: Endpoint `POST /analysis/job` to force-run a specific URL. |

---

## ⚙️ How It Works (The Loop)

1.  **Fetch**: Server calls `STARTUP_JOB_URL`.
2.  **Extract**: Looks for `media_url` or `s3_url` in the JSON response.
3.  **Download**: Saves the file temporarily.
4.  **Analyze**:
    *   **Video**: Activity Recognition (YOLO) + Transcription.
    *   **Audio**: Transcription Only.
5.  **Sleep**: Waits `JOB_INTERVAL_MINUTES` before repeating.

> **Note**: Legacy features (Live Chat, UI, WebRTC) are currently disabled in `main.py`.
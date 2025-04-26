# YouTube Playlist Monitor

A full‐stack application that tracks the size and total duration of a YouTube playlist over time. The **Python** backend fetches playlist data daily via the YouTube Data API and stores it in **Firestore**. The **React** frontend reads that data and displays:

- Historical charts of video count and total minutes  
- Summary statistics (daily/weekly/monthly changes, averages, indicators)  
- Status of the last fetch  

---

## Features

- **Daily data collection**  
  - Automatically fetches videos in a playlist  
  - Parses ISO‐8601 durations into minutes  
  - Stores “video count” and “total minutes” per day  
- **Data processing & analytics**  
  - Computes day/week/month changes (added/removed)  
  - Calculates averages and change indicators (up/down/steady)  
  - Persists pre‐processed points and calculated stats  
- **Interactive frontend**  
  - Displays status and timestamp of last successful fetch  
  - Summarizes current values and change indicators  
  - Renders line charts for videos and minutes (last 28 days)  
- **Firebase integration** for both backend (Firestore) and frontend

---

## Tech Stack

- **Backend**  
  - Python 3.8+  
  - [google-api-python-client](https://github.com/googleapis/google-api-python-client)  
  - [python-dotenv](https://github.com/theskumar/python-dotenv)  
  - [google-cloud-firestore](https://github.com/googleapis/python-firestore)  
- **Frontend**  
  - React + Vite  
  - TypeScript  
  - Firebase JS SDK (Firestore)   

---

## Prerequisites

1. **YouTube Data API v3** enabled  
2. **Firebase** project with Firestore  
3. **Node.js** & **npm** (or Yarn)  
4. **Python 3.8+**  

---

## Configuration

### Backend

Create a `.env` at the repo root:

```dotenv
PLAYLIST_ID=YOUR_YOUTUBE_PLAYLIST_ID
YOUTUBE_API_KEY=YOUR_YOUTUBE_DATA_API_KEY
FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccount.json
# Or paste the JSON credentials directly as a SINGLE env var
```

- `PLAYLIST_ID` – ID of the YouTube playlist to monitor (excluding the 'https://www.youtube.com/playlist?list=' part)  
- `YOUTUBE_API_KEY` – Key for YouTube Data API v3  
- `FIREBASE_CREDENTIALS_PATH` – Either a local path or the JSON content
  - If you are testing locally, use the path for the 'serviceAccount.json' file  
  - If you are hosting on GitHub, for example, use the JSON credentials as the string on the environment secret

### Frontend

For the frontend, add on the `.env`:

```dotenv
VITE_API_KEY=your_firebase_api_key
VITE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_PROJECT_ID=your_project_id
VITE_STORAGE_BUCKET=your_project.appspot.com
VITE_MESSAGING_SENDER_ID=messaging_sender_id
VITE_APP_ID=app_id
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/LorenzoCW/YouTube-Playlist-Monitor.git
cd YouTube-Playlist-Monitor
```

### 2. Backend

```bash
# (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python backend/save_data.py
```

- `save_data.py` will:
  1. Check if today’s data already exists in Firestore  
  2. Fetch playlist video IDs & durations  
  3. Upload `video_count` & `total_minutes` for today  
  4. Compute parsed points and analytics  
  5. Save results under `parsed_data` & `status` collections

### 3. Scheduling with GitHub Actions

A workflow is pre‑configured at .github/workflows/run-save-data.yml to run backend/save_data.py every day at 03:00 UTC (00:00 BRT). You don’t need to set up a local cron job - just commit and push your changes.

### 4. Frontend

```bash
npm install
npm run dev
```

- Open <http://localhost:5173> to view the dashboard.

---

### Dashboard Overview

![dashboard](/screenshots/dashboard.png)

---

## Contributing

1. Fork the repo  
2. Create a feature branch (`git checkout -b feature/xyz`)  
3. Commit your changes (`git commit -m 'Add xyz'`)  
4. Push (`git push origin feature/xyz`)  
5. Open a Pull Request  

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
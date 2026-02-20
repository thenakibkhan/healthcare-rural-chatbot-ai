# RuralHealth AI - Deployment Instructions

## Prerequisites
- Python 3.8 or higher installed.

## Setup & Running

1. **Open a terminal** in this folder.
2. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. **Run the application**:
   - Double-click `run_app.bat` (if created) OR run:
   ```bash
   python backend/app.py
   ```
4. **Open your browser**:
   - Go to [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Features
- **Disease Prediction**: Enter symptoms to get a diagnosis.
- **Multilingual**: Switch between English, Hindi, and Tamil.
- **PDF Reports**: Download a detailed health report.
- **Login**: Mock login system (uses email/password or Google button).

## Troubleshooting
- If `pip` is not recognized, ensure Python is added to your PATH.
- If the browser doesn't open, manually type the address.
- Ensure `backend/ml/dataset` files are present.

## Deployment (Render/Heroku)
The project includes a `Procfile` for deployment on platforms like Render or Heroku.
1. **Push to GitHub or GitLab**.
2. **Connect Repository** to your hosting provider.
3. **Build Command**: `pip install -r backend/requirements.txt`
4. **Start Command**: `gunicorn backend.app:app` (Note: adjust path if needed, or move app.py to root if platform requires)
   - Current Procfile points to `web: gunicorn backend.app:app` assuming root is `d:/final project`.
   - Wait, `Procfile` content was `web: gunicorn app:app`. But `app.py` is in `backend/`.
   - I need to check `Procfile` content again. If `app.py` is in `backend/`, then `gunicorn` might need to be run from `backend` directory or module path.
   - Let's check `d:/final project/backend/app.py`.
   - If root is `d:/final project`, then `gunicorn backend.app:app` is correct.
   - But if user deploys `backend` folder as root, then `gunicorn app:app`.
   - Usually people deploy the whole repo.
   - Let's correct `Procfile` to `web: cd backend && gunicorn app:app` or similar? Or just `web: gunicorn --chdir backend app:app`.
   - I'll update `Procfile` first.


# CareCircle

CareCircle – Trusted Support for Independent Elderly Living

## Overview
This project is a Flask-based MVP for a care coordination platform that helps elderly people and their families arrange trusted, verified support.

## Features
- Elderly web dashboard
- Family member workflow for dedicated care
- Verified helper onboarding and verification
- Help requests and matching
- Appointment and medicine reminder features
- Care communication and chatbot
- Notifications and admin dashboard

## Run locally

PowerShell commands:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000/

## Deploy

Set the deployment service's root directory to `carecircle` and use the start command:

```text
gunicorn app:app --bind 0.0.0.0:$PORT
```

The included `Procfile` contains the same command. The service must be a Python web service, not a static-site or GitHub Pages deployment.

## Demo accounts
- Admin: admin@carecircle.com / admin123
- Elderly: lakshmi@carecircle.com / lakshmi123
- Family: anjali@carecircle.com / anjali123
- Helper: anitha@carecircle.com / anitha123

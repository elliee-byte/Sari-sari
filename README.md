# Sari-Sari Tech

A Flask + SQLite starter for an independent TUP Manila student marketplace.

## Included in this first working version
- Responsive homepage and marketplace
- Predefined product categories
- Search, category, condition, price, and status filters
- Product detail pages
- Student account registration and login
- One account can browse and sell
- Create, edit, and delete your own listings
- Up to five product photos (local upload)
- Favorites for logged-in users
- Available / Reserved / Sold listing states
- Sold listings are excluded from public marketplace results
- SQLite database and automatic starter-category seeding

## Requirements
- Python 3.10 or newer
- VS Code (recommended)

## Run on Windows
1. Extract the ZIP file.
2. Open the `sari_sari_tech` folder in VS Code.
3. Open Terminal > New Terminal.
4. Create a virtual environment:

   `py -m venv .venv`

5. Activate it:

   PowerShell: `.venv\\Scripts\\Activate.ps1`

   If PowerShell blocks activation, use Command Prompt:
   `.venv\\Scripts\\activate.bat`

6. Install packages:

   `python -m pip install -r requirements.txt`

7. Start the website:

   `python run.py`

8. Open `http://127.0.0.1:5000` in your browser.

The database is created automatically on first run.

## Important prototype notes
- This is the first development milestone, not the complete production platform.
- Registration currently creates an email-unverified, eligibility-pending account. The SMTP verification and separate student eligibility approval workflow still need to be implemented before real public use.
- Do not use real student information for public demonstrations yet.
- The default secret key is for local development only. Set a strong `SECRET_KEY` in `.env` before deployment.
- Images are stored locally in `uploads/`. A hosted deployment will need persistent storage.
- Payment, delivery, and in-app messaging are intentionally not included. Buyers and sellers arrange transactions independently.
- Admin moderation, reports, announcements, notification center, saved searches, password reset, and production email verification are planned for later milestones.

## Project structure
```text
sari_sari_tech/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   ├── routes.py
│   ├── templates/
│   └── static/
├── instance/
├── uploads/
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

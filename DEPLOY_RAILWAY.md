# Deploy to Railway

1. Create a GitHub repository and upload this project folder (the folder containing `app.py`).
2. In Railway, create a new project and choose **Deploy from GitHub repo**.
3. Add a **PostgreSQL** service to the same Railway project.
4. In the Flask service Variables, make sure `DATABASE_URL` references the PostgreSQL service's `DATABASE_URL` variable.
5. Add these Flask service variables:
   - `SECRET_KEY` = a long random value
   - `ADMIN_USERNAME` = your manager username
   - `ADMIN_PASSWORD` = a strong manager password
   - `ADMIN_FULL_NAME` = manager display name
6. Railway will install `requirements.txt` and start the app with `gunicorn app:app`.
7. In Flask service Settings > Networking, generate a public domain.
8. Open the generated HTTPS URL. `/` redirects to Login.
9. Verify `https://YOUR-DOMAIN/health` returns database `connected`.

Important: the existing starter advisor passwords are development credentials. Change them before real business use.

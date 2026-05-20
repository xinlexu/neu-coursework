# Week 6

Run locally:

- Backend:
  ```bash
  cd backend
  python3 -m venv ../.venv && source ../.venv/bin/activate
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py runserver 8000
  ```
- Frontend:
  ```bash
  cd frontend
  npm install
  npm start
  ```

Open http://localhost:3000

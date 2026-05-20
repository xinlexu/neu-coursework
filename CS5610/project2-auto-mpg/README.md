# Student · CS5610 · Project 2 — Auto MPG

Train a regression model and estimate car MPG.

## Stack
- **Frontend:** React + Vite (TypeScript)
- **Backend:** FastAPI (Python 3.11+), scikit‑learn
- **DB:** PostgreSQL (SQLAlchemy)
- **Data:** offline CSV at `backend/data/auto-mpg.csv`

## Folder layout
```
project2-auto-mpg/
  backend/
    app/
      data_bootstrap.py
      deps.py
      main.py
      models_db.py
      schemas.py
      ml/
        datasets.py
        predict.py
        trainer.py
    data/auto-mpg.csv
    models/                # trained models (exp_*.joblib)
    requirements.txt
    .env.example
  frontend/
    public/
      project2.png
    src/
      api.ts
      App.tsx
      main.tsx
      styles.css
      pages/
        Home.tsx
        Train.tsx
        Estimate.tsx
    index.html
    package.json
    tsconfig.json
    vite.config.ts
  README.md
```


## Prerequisites
- Python **3.11+**
- Node.js **18+**
- PostgreSQL **14+** running on `localhost:5432`
- Database named **`autompg`**

Create DB:
```bash
# psql
psql -U postgres -h localhost -c "CREATE DATABASE autompg;"
```

## Backend
```powershell
# Windows PowerShell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# connection
$env:DATABASE_URL="postgresql+psycopg2://postgres:<password>@localhost:5432/autompg"

python -m uvicorn app.main:app --reload --port 8000
# Health: http://localhost:8000/health  -> {"ok": true}
```

```bash
# macOS / Linux
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

export DATABASE_URL="postgresql+psycopg2://postgres:<password>@localhost:5432/autompg"
python -m uvicorn app.main:app --reload --port 8000
```

## Frontend
```bash
cd frontend
npm install
npm run dev
# open the URL from the terminal (usually http://localhost:5173)
```

## How to use
1) **Train** page → choose model (Linear / Random Forest) → **Train**.  
   The response includes an **`experiment_id`** and metrics (MSE, MAE, R²).  
2) **Estimate** page → enter the `experiment_id` → fill all fields → **Predict**.  
   The app returns predicted **MPG** and an interval.  
3) Runs are stored in PostgreSQL:
   - `experiments` (each training)
   - `predictions` (each prediction)

## Troubleshooting
- **experiment not found** → Train first and use the returned id.
- **Dataset error** → Ensure `backend/data/auto-mpg.csv` exists with columns:  
  `mpg, cylinders, displacement, horsepower, weight, acceleration, model_year, origin`.
- **Cannot start uvicorn** → use `python -m uvicorn ...` inside the venv.
- **Frontend not updating** → restart dev server: `Ctrl+C` then `npm run dev`.

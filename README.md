# Poultry Disease Prevention & Vaccination Management System

A full-stack AI-powered web application built with **Flask + MySQL + XGBoost**.

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.9+
- MySQL Server (running locally)
- MySQL Workbench (optional, for DB management)

### 2. Create the MySQL Database
Open MySQL Workbench or MySQL CLI and run:
```sql
CREATE DATABASE IF NOT EXISTS poultry_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Configure `.env`
Edit the `.env` file in the project root:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_root_password
DB_NAME=poultry_db
SECRET_KEY=poultry-secret-key-change-in-production-2024
```

### 4. Install Python Dependencies
```bash
cd "C:\Users\Preeti Pujari\OneDrive\Documents\poultry"
pip install -r requirements.txt
```

### 5. Train ML Models (one time only)
```bash
python ml_models/train_models.py
```
This generates:
- `ml_models/xgboost_model.joblib` (XGBoost – ~88% accuracy)
- `ml_models/decision_tree_model.joblib` (Decision Tree – ~80% accuracy)
- `ml_models/preprocessor.joblib`
- `ml_models/label_encoder.joblib`
- `ml_models/model_metrics.json`
- `dataset/poultry_disease_dataset.csv`

### 6. Run the Application
```bash
python run.py
```
Then open: **http://localhost:5000**

---

## 🔐 Default Credentials

| Role  | Username/Email | Password |
|-------|---------------|----------|
| Admin | `admin`       | `admin123` |
| Farmer | Register at `/register` | — |

---

## 📁 Project Structure

```
poultry/
├── app.py                  # App factory, blueprints, DB seeding
├── run.py                  # Entry point
├── config.py               # Flask config (reads .env)
├── .env                    # DB credentials (edit this!)
├── requirements.txt
│
├── models/                 # SQLAlchemy ORM models
│   ├── user.py             # Admin, Farmer
│   ├── farm.py             # PoultryFarm
│   ├── batch.py            # PoultryBatch, PoultryBreed
│   ├── health.py           # PoultryHealthRecord
│   ├── disease.py          # Disease, DiseasePrediction
│   └── vaccination.py      # VaccinationRecord, VaccinationSchedule
│
├── routes/                 # Flask blueprints
│   ├── auth_routes.py      # Login, Register, Logout
│   ├── admin_routes.py     # Admin CRUD + Reports
│   ├── farmer_routes.py    # Farmer dashboard
│   ├── farm_routes.py      # Farm CRUD
│   ├── batch_routes.py     # Batch CRUD
│   ├── health_routes.py    # Health Record CRUD
│   ├── prediction_routes.py# AI Disease Prediction
│   ├── vaccination_routes.py # Vaccination + Calendar
│   └── report_routes.py    # Reports + CSV export
│
├── services/
│   ├── prediction_service.py   # XGBoost + DT inference
│   └── recommendation_service.py # Disease recommendations
│
├── ml_models/
│   ├── train_models.py     # Training script
│   ├── xgboost_model.joblib     (generated after training)
│   ├── decision_tree_model.joblib (generated after training)
│   ├── preprocessor.joblib      (generated after training)
│   ├── label_encoder.joblib     (generated after training)
│   └── model_metrics.json       (generated after training)
│
├── templates/              # Jinja2 HTML templates
│   ├── base_admin.html
│   ├── base_farmer.html
│   ├── auth/               login.html, register.html
│   ├── admin/              dashboard, farmers, farms, batches, ...
│   ├── farmer/             dashboard.html
│   ├── farms/              list, form, view
│   ├── batches/            list, form, view
│   ├── health/             list, form, view
│   ├── predictions/        form, result, history
│   ├── vaccinations/       list, form, calendar
│   └── reports/            home, health_summary, ...
│
├── static/
│   └── css/main.css        # Custom dark-green theme
│
├── database/
│   └── schema.sql          # Complete MySQL schema (reference)
│
└── dataset/
    └── poultry_disease_dataset.csv (generated after training)
```

---

## 🌿 Features

### Admin Module
- Full CRUD: Farmers, Farms, Batches, Health Records, Diseases
- Monitoring: AI Predictions, Vaccinations
- Reports & Analytics with charts

### Farmer Module
- Dashboard with live stats (farms, batches, birds, health, predictions, vaccinations)
- Farm & Batch management (CRUD)
- Health Record management with mortality validation
- **AI Disease Prediction** (XGBoost + Decision Tree)
- Vaccination management + dynamic calendar (prev/next month navigation)
- CSV export for health & vaccination records

### AI Disease Prediction
Predicts 8 disease classes:
- Healthy, Newcastle Disease, Avian Influenza, Infectious Bursal Disease (Gumboro)
- Marek's Disease, Coccidiosis, Infectious Bronchitis, Fowl Cholera

> **Disclaimer**: ML predictions are preliminary screening results only. They are NOT veterinary diagnoses. Always consult a licensed veterinarian.

---

## 🗄️ Database Tables
1. `admins` — Admin accounts
2. `farmers` — Farmer accounts
3. `poultry_farms` — Farm records
4. `poultry_batches` — Batch records
5. `poultry_breeds` — Breed reference
6. `poultry_health_records` — Health monitoring
7. `diseases` — Disease reference data
8. `disease_predictions` — ML prediction history
9. `vaccination_records` — Vaccination tracking
10. `vaccination_schedules` — Schedule templates

---

## 🎨 Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | Python 3.9, Flask 3.1 |
| Database | MySQL 8+, SQLAlchemy 2.0 |
| ML | XGBoost 2.1, Decision Tree, scikit-learn 1.6 |
| Frontend | Bootstrap 5.3, Chart.js, Bootstrap Icons, Font Awesome 6 |
| Security | Werkzeug hashing, Flask-Login, Flask-WTF CSRF |

---

## 🛠️ Troubleshooting

**MySQL connection error**: Update `DB_PASSWORD` in `.env` with your MySQL root password.

**ML models not found**: Run `python ml_models/train_models.py` from the project root.

**Tables not created**: The app creates tables automatically on first run via `db.create_all()`.

**Port 5000 in use**: Change `port=5000` in `run.py` to another port like `5001`.


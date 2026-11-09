"""
Poultry Disease Dataset Generator and ML Model Trainer
=======================================================

IMPORTANT DISCLAIMER:
This script generates a SYNTHETIC training dataset based on documented
clinical parameters from established veterinary references:

  1. FAO Animal Health Manual No. 1 - "Manual on the Diagnosis of Poultry Diseases"
  2. Merck Veterinary Manual - Poultry section (msdvetmanual.com)
  3. "Poultry Diseases" by Frank Jordan, Mark Pattison et al. (6th Edition)
  4. OIE (WOAH) Terrestrial Manual - Chapters on Newcastle Disease, Avian Influenza,
     Infectious Bursal Disease, Marek's Disease, Coccidiosis

The parameter ranges (temperature, mortality, feed consumption, age susceptibility)
are derived from published clinical descriptions in these references.

THIS SYNTHETIC DATA IS INTENDED ONLY FOR DEMONSTRATION OF THE APPLICATION WORKFLOW.
In a production system, real clinical and laboratory-confirmed case data must be used.
Refer to the README for guidance on using real datasets.

The models trained here are illustrative screening tools ONLY.
They are NOT substitutes for veterinary diagnosis.

Usage:
    python ml_models/train_models.py
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime

# Ensure we can import from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, classification_report, confusion_matrix)
from xgboost import XGBClassifier
import joblib

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(os.path.dirname(MODEL_DIR), 'dataset')


# ─── SYNTHETIC DATASET GENERATION ─────────────────────────────────────────────

def generate_synthetic_dataset(n_samples=3000, random_state=42):
    """
    Generate a synthetic dataset based on documented poultry health parameters.

    Features:
      bird_age_weeks, body_temperature, feed_consumption_kg (per 100 birds/day),
      water_consumption_litres (per 100 birds/day), bird_weight_kg (avg),
      mortality_count (per 100 birds), mortality_rate (%),
      temp_above_42 (binary), low_feed (binary), poultry_type_encoded

    Target: disease_label
    """
    np.random.seed(random_state)
    rng = np.random.default_rng(random_state)

    # Disease class definitions with parameter distributions
    # Based on documented clinical presentations
    disease_configs = {
        'Healthy': {
            'weight': 0.25,
            'age_range': (1, 52),
            'temp_range': (40.6, 41.8),   # Normal avian: 40.5–42°C
            'feed_factor': (0.85, 1.15),
            'water_factor': (0.90, 1.10),
            'mortality_range': (0, 2),
            'weight_factor': (0.90, 1.10)
        },
        'Newcastle Disease': {
            'weight': 0.15,
            'age_range': (2, 52),
            'temp_range': (42.0, 44.0),   # Elevated in acute ND
            'feed_factor': (0.1, 0.5),    # Severely reduced intake
            'water_factor': (0.2, 0.6),
            'mortality_range': (5, 50),   # Can be very high in velogenic
            'weight_factor': (0.5, 0.85)
        },
        'Infectious Bursal Disease': {
            'weight': 0.12,
            'age_range': (3, 8),          # Primarily 3–6 weeks
            'temp_range': (40.0, 42.5),
            'feed_factor': (0.3, 0.7),
            'water_factor': (0.5, 0.9),
            'mortality_range': (5, 30),
            'weight_factor': (0.6, 0.90)
        },
        'Avian Influenza': {
            'weight': 0.10,
            'age_range': (1, 52),
            'temp_range': (42.5, 44.5),   # High fever, HPAI
            'feed_factor': (0.05, 0.3),
            'water_factor': (0.1, 0.4),
            'mortality_range': (20, 100),  # HPAI near 100%
            'weight_factor': (0.3, 0.7)
        },
        'Marek\'s Disease': {
            'weight': 0.10,
            'age_range': (12, 30),         # 12–30 weeks typical
            'temp_range': (40.5, 42.0),
            'feed_factor': (0.5, 0.8),
            'water_factor': (0.6, 0.9),
            'mortality_range': (1, 15),
            'weight_factor': (0.4, 0.75)   # Weight loss prominent
        },
        'Coccidiosis': {
            'weight': 0.13,
            'age_range': (2, 10),          # Young birds most susceptible
            'temp_range': (40.5, 42.0),
            'feed_factor': (0.4, 0.7),
            'water_factor': (0.6, 1.0),
            'mortality_range': (2, 25),
            'weight_factor': (0.5, 0.80)
        },
        'Infectious Bronchitis': {
            'weight': 0.08,
            'age_range': (1, 52),
            'temp_range': (40.5, 42.5),
            'feed_factor': (0.5, 0.80),
            'water_factor': (0.6, 0.90),
            'mortality_range': (1, 10),
            'weight_factor': (0.70, 0.95)
        },
        'Fowl Cholera': {
            'weight': 0.07,
            'age_range': (4, 52),
            'temp_range': (42.0, 43.5),
            'feed_factor': (0.2, 0.6),
            'water_factor': (0.3, 0.7),
            'mortality_range': (10, 60),
            'weight_factor': (0.5, 0.80)
        },
    }

    # Poultry type encoding
    poultry_types = ['Broiler', 'Layer', 'Turkey', 'Duck', 'Quail', 'Geese', 'Other']
    poultry_type_map = {t: i for i, t in enumerate(poultry_types)}

    # Normal feed/water baselines per 100 birds per day (kg / litres)
    # Broilers: ~10 kg feed, 20 L water per 100 birds/day at typical age
    baseline_feed_per_100 = 10.0
    baseline_water_per_100 = 20.0
    baseline_weight_kg = 1.8  # average broiler at 6 weeks

    records = []
    disease_names = list(disease_configs.keys())
    weights = [disease_configs[d]['weight'] for d in disease_names]
    # Normalize weights
    total_w = sum(weights)
    weights = [w / total_w for w in weights]

    for _ in range(n_samples):
        disease = rng.choice(disease_names, p=weights)
        cfg = disease_configs[disease]

        age = rng.integers(cfg['age_range'][0], cfg['age_range'][1] + 1)
        temp = rng.uniform(cfg['temp_range'][0], cfg['temp_range'][1])

        # Feed/water scaled by age (older birds eat more) and disease factor
        age_feed_scale = min(age / 6.0, 2.5)
        feed_factor = rng.uniform(cfg['feed_factor'][0], cfg['feed_factor'][1])
        water_factor = rng.uniform(cfg['water_factor'][0], cfg['water_factor'][1])
        feed_kg = round(baseline_feed_per_100 * age_feed_scale * feed_factor, 2)
        water_l = round(baseline_water_per_100 * age_feed_scale * water_factor, 2)

        # Weight
        weight_factor = rng.uniform(cfg['weight_factor'][0], cfg['weight_factor'][1])
        bird_weight = round(baseline_weight_kg * weight_factor * (age / 6.0), 3)
        bird_weight = max(0.05, bird_weight)

        # Mortality (per 100 birds)
        mortality = int(rng.integers(cfg['mortality_range'][0], cfg['mortality_range'][1] + 1))
        mortality_rate = round(mortality, 2)

        # Derived features
        temp_above_42 = 1 if temp > 42.0 else 0
        expected_feed = baseline_feed_per_100 * age_feed_scale
        low_feed = 1 if feed_kg < expected_feed * 0.5 else 0

        poultry_type = rng.choice(poultry_types)
        poultry_type_encoded = poultry_type_map[poultry_type]

        records.append({
            'bird_age_weeks': age,
            'body_temperature': round(temp, 2),
            'feed_consumption_kg': feed_kg,
            'water_consumption_litres': water_l,
            'bird_weight_kg': bird_weight,
            'mortality_count': mortality,
            'mortality_rate': mortality_rate,
            'temp_above_42': temp_above_42,
            'low_feed': low_feed,
            'poultry_type_encoded': poultry_type_encoded,
            'disease_label': disease
        })

    df = pd.DataFrame(records)
    return df


# ─── TRAINING PIPELINE ────────────────────────────────────────────────────────

def train_and_evaluate():
    print("=" * 60)
    print("Poultry Disease ML Model Training Pipeline")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Generate (or load) dataset
    dataset_path = os.path.join(DATASET_DIR, 'poultry_disease_dataset.csv')
    os.makedirs(DATASET_DIR, exist_ok=True)

    print("Generating synthetic dataset (3000 samples)...")
    df = generate_synthetic_dataset(n_samples=3000)
    df.to_csv(dataset_path, index=False)
    print(f"Dataset saved to: {dataset_path}")
    print(f"Dataset shape: {df.shape}")
    print(f"\nClass distribution:")
    print(df['disease_label'].value_counts())
    print()

    # Feature columns (must match prediction_service.py exactly)
    FEATURE_COLS = [
        'bird_age_weeks', 'body_temperature', 'feed_consumption_kg',
        'water_consumption_litres', 'bird_weight_kg', 'mortality_count',
        'mortality_rate', 'temp_above_42', 'low_feed', 'poultry_type_encoded'
    ]
    TARGET_COL = 'disease_label'

    # Validate dataset
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values

    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    print(f"Classes: {list(le.classes_)}")
    print(f"Number of classes: {len(le.classes_)}")
    print()

    # Train-test split (80/20, stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")

    # Preprocessing (StandardScaler)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ── XGBoost ───────────────────────────────────────────────────────────────
    print("\nTraining XGBoost Classifier...")
    xgb_model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='mlogloss',
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(X_train_scaled, y_train)
    y_pred_xgb = xgb_model.predict(X_test_scaled)

    xgb_metrics = {
        'accuracy': round(float(accuracy_score(y_test, y_pred_xgb)), 4),
        'precision': round(float(precision_score(y_test, y_pred_xgb, average='weighted', zero_division=0)), 4),
        'recall': round(float(recall_score(y_test, y_pred_xgb, average='weighted', zero_division=0)), 4),
        'f1_score': round(float(f1_score(y_test, y_pred_xgb, average='weighted', zero_division=0)), 4),
    }

    print(f"\nXGBoost Results:")
    print(f"  Accuracy:  {xgb_metrics['accuracy']:.4f} ({xgb_metrics['accuracy']*100:.2f}%)")
    print(f"  Precision: {xgb_metrics['precision']:.4f}")
    print(f"  Recall:    {xgb_metrics['recall']:.4f}")
    print(f"  F1-Score:  {xgb_metrics['f1_score']:.4f}")
    print("\nClassification Report (XGBoost):")
    print(classification_report(y_test, y_pred_xgb, target_names=le.classes_, zero_division=0))

    # ── Decision Tree ─────────────────────────────────────────────────────────
    print("\nTraining Decision Tree Classifier...")
    dt_model = DecisionTreeClassifier(
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=42
    )
    dt_model.fit(X_train_scaled, y_train)
    y_pred_dt = dt_model.predict(X_test_scaled)

    dt_metrics = {
        'accuracy': round(float(accuracy_score(y_test, y_pred_dt)), 4),
        'precision': round(float(precision_score(y_test, y_pred_dt, average='weighted', zero_division=0)), 4),
        'recall': round(float(recall_score(y_test, y_pred_dt, average='weighted', zero_division=0)), 4),
        'f1_score': round(float(f1_score(y_test, y_pred_dt, average='weighted', zero_division=0)), 4),
    }

    print(f"\nDecision Tree Results:")
    print(f"  Accuracy:  {dt_metrics['accuracy']:.4f} ({dt_metrics['accuracy']*100:.2f}%)")
    print(f"  Precision: {dt_metrics['precision']:.4f}")
    print(f"  Recall:    {dt_metrics['recall']:.4f}")
    print(f"  F1-Score:  {dt_metrics['f1_score']:.4f}")
    print("\nClassification Report (Decision Tree):")
    print(classification_report(y_test, y_pred_dt, target_names=le.classes_, zero_division=0))

    # ── Save models and artifacts ─────────────────────────────────────────────
    os.makedirs(MODEL_DIR, exist_ok=True)

    xgb_path = os.path.join(MODEL_DIR, 'xgboost_model.joblib')
    dt_path = os.path.join(MODEL_DIR, 'decision_tree_model.joblib')
    scaler_path = os.path.join(MODEL_DIR, 'preprocessor.joblib')
    le_path = os.path.join(MODEL_DIR, 'label_encoder.joblib')
    metrics_path = os.path.join(MODEL_DIR, 'model_metrics.json')

    joblib.dump(xgb_model, xgb_path)
    joblib.dump(dt_model, dt_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(le, le_path)

    # Confusion matrices (convert to lists for JSON serialization)
    cm_xgb = confusion_matrix(y_test, y_pred_xgb).tolist()
    cm_dt = confusion_matrix(y_test, y_pred_dt).tolist()

    metrics = {
        'trained_at': datetime.now().isoformat(),
        'dataset': {
            'source': 'Synthetic dataset based on FAO/Merck veterinary references',
            'total_samples': len(df),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'classes': list(le.classes_),
            'features': FEATURE_COLS
        },
        'disclaimer': (
            'This model was trained on a SYNTHETIC dataset for demonstration purposes. '
            'Results are NOT clinical diagnoses. Always consult a veterinarian.'
        ),
        'xgboost': {**xgb_metrics, 'confusion_matrix': cm_xgb},
        'decision_tree': {**dt_metrics, 'confusion_matrix': cm_dt}
    }

    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print("\n" + "=" * 60)
    print("Training Complete! Files saved:")
    print(f"  {xgb_path}")
    print(f"  {dt_path}")
    print(f"  {scaler_path}")
    print(f"  {le_path}")
    print(f"  {metrics_path}")
    print(f"  {dataset_path}")
    print("=" * 60)

    return metrics


if __name__ == '__main__':
    train_and_evaluate()


"""
Poultry Disease Prediction Service

Uses a pre-trained XGBoost and Decision Tree classifier to predict
common poultry diseases based on health parameters.

Dataset source: Synthetic dataset generated from documented poultry health
parameters described in:
  - FAO Animal Health Manual: Poultry Diseases
  - Merck Veterinary Manual (Poultry section)
  - "Poultry Diseases" by Frank Jordan et al. (6th Ed.)

DISCLAIMER: ML predictions are preliminary screening tools only.
They are NOT veterinary diagnoses. Always consult a licensed veterinarian.
"""

import os
import joblib
import numpy as np
import json

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_models')
XGBOOST_MODEL_PATH = os.path.join(MODEL_DIR, 'xgboost_model.joblib')
DT_MODEL_PATH = os.path.join(MODEL_DIR, 'decision_tree_model.joblib')
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, 'preprocessor.joblib')
LABEL_ENCODER_PATH = os.path.join(MODEL_DIR, 'label_encoder.joblib')
METRICS_PATH = os.path.join(MODEL_DIR, 'model_metrics.json')

_xgboost_model = None
_dt_model = None
_preprocessor = None
_label_encoder = None


def _load_models():
    global _xgboost_model, _dt_model, _preprocessor, _label_encoder
    if _xgboost_model is None and os.path.exists(XGBOOST_MODEL_PATH):
        _xgboost_model = joblib.load(XGBOOST_MODEL_PATH)
    if _dt_model is None and os.path.exists(DT_MODEL_PATH):
        _dt_model = joblib.load(DT_MODEL_PATH)
    if _preprocessor is None and os.path.exists(PREPROCESSOR_PATH):
        _preprocessor = joblib.load(PREPROCESSOR_PATH)
    if _label_encoder is None and os.path.exists(LABEL_ENCODER_PATH):
        _label_encoder = joblib.load(LABEL_ENCODER_PATH)


def models_available():
    return (os.path.exists(XGBOOST_MODEL_PATH) and
            os.path.exists(DT_MODEL_PATH) and
            os.path.exists(PREPROCESSOR_PATH) and
            os.path.exists(LABEL_ENCODER_PATH))


def get_model_metrics():
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, 'r') as f:
            return json.load(f)
    return {}


def _build_feature_vector(params: dict) -> np.ndarray:
    """
    Build a feature vector from health parameters.
    Feature order must match training pipeline exactly.

    Features:
    0  bird_age_weeks
    1  body_temperature
    2  feed_consumption_kg
    3  water_consumption_litres
    4  bird_weight_kg
    5  mortality_count
    6  mortality_rate  (derived)
    7  temp_above_42   (binary: temp > 42°C)
    8  low_feed        (binary: feed_consumption < 50% of normal)
    9  poultry_type_encoded
    """
    bird_age = float(params.get('bird_age_weeks', 0) or 0)
    body_temp = float(params.get('body_temperature', 41.0) or 41.0)
    feed_kg = float(params.get('feed_consumption_kg', 0) or 0)
    water_l = float(params.get('water_consumption_litres', 0) or 0)
    bird_weight = float(params.get('bird_weight_kg', 0) or 0)
    mortality = float(params.get('mortality_count', 0) or 0)
    num_birds = float(params.get('number_of_birds', 1) or 1)

    mortality_rate = (mortality / num_birds) * 100 if num_birds > 0 else 0
    temp_above_42 = 1 if body_temp > 42.0 else 0
    # Normal feed for broilers: ~1 kg per 10 birds/day
    expected_feed = num_birds * 0.1
    low_feed = 1 if (expected_feed > 0 and feed_kg < expected_feed * 0.5) else 0

    # Encode poultry type
    poultry_type_map = {'Broiler': 0, 'Layer': 1, 'Turkey': 2, 'Duck': 3,
                        'Quail': 4, 'Geese': 5, 'Other': 6}
    poultry_type_encoded = poultry_type_map.get(params.get('poultry_type', 'Broiler'), 0)

    features = np.array([[
        bird_age, body_temp, feed_kg, water_l, bird_weight,
        mortality, mortality_rate, temp_above_42, low_feed,
        poultry_type_encoded
    ]], dtype=np.float32)

    return features


def predict_disease(params: dict) -> dict:
    """
    Run both models and return a prediction result dict.

    Returns:
        dict with keys:
          xgboost_prediction, xgboost_confidence,
          decision_tree_prediction, decision_tree_confidence,
          final_prediction, agreement, models_used
    """
    _load_models()

    if not models_available():
        return {
            'error': 'ML models have not been trained yet. Please run train_models.py first.',
            'models_available': False
        }

    try:
        features = _build_feature_vector(params)

        if _preprocessor is not None:
            features = _preprocessor.transform(features)

        # XGBoost prediction
        xgb_pred_encoded = _xgboost_model.predict(features)[0]
        xgb_proba = _xgboost_model.predict_proba(features)[0]
        xgb_confidence = float(np.max(xgb_proba)) * 100

        # Decision Tree prediction
        dt_pred_encoded = _dt_model.predict(features)[0]
        dt_proba = _dt_model.predict_proba(features)[0]
        dt_confidence = float(np.max(dt_proba)) * 100

        # Decode labels
        if _label_encoder is not None:
            xgb_disease = _label_encoder.inverse_transform([int(xgb_pred_encoded)])[0]
            dt_disease = _label_encoder.inverse_transform([int(dt_pred_encoded)])[0]
        else:
            xgb_disease = str(xgb_pred_encoded)
            dt_disease = str(dt_pred_encoded)

        # Final prediction: use higher-confidence model
        if xgb_confidence >= dt_confidence:
            final_prediction = xgb_disease
        else:
            final_prediction = dt_disease

        agreement = xgb_disease == dt_disease

        return {
            'xgboost_prediction': xgb_disease,
            'xgboost_confidence': round(xgb_confidence, 2),
            'decision_tree_prediction': dt_disease,
            'decision_tree_confidence': round(dt_confidence, 2),
            'final_prediction': final_prediction,
            'agreement': agreement,
            'models_available': True,
            'error': None
        }

    except Exception as e:
        return {
            'error': f'Prediction error: {str(e)}',
            'models_available': True
        }


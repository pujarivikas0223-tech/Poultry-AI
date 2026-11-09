from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from models.farm import PoultryFarm
from models.batch import PoultryBatch
from models.disease import Disease, DiseasePrediction
from routes.decorators import farmer_required
from services.prediction_service import predict_disease, models_available, get_model_metrics
from services.recommendation_service import get_recommendations

prediction_bp = Blueprint('prediction', __name__)


def _get_farmer_batches():
    farms = PoultryFarm.query.filter_by(farmer_id=current_user.id).all()
    farm_ids = [f.id for f in farms]
    if not farm_ids:
        return []
    return PoultryBatch.query.filter(
        PoultryBatch.farm_id.in_(farm_ids),
        PoultryBatch.is_active == True
    ).all()


@prediction_bp.route('/', endpoint='prediction_history')
@prediction_bp.route('/history')
@prediction_bp.route('/list', endpoint='list_predictions')
@login_required
@farmer_required
def prediction_history():
    predictions = (DiseasePrediction.query
                   .filter_by(farmer_id=current_user.id)
                   .order_by(DiseasePrediction.prediction_date.desc())
                   .all())
    return render_template('predictions/history.html',
                           predictions=predictions,
                           models_ready=models_available(),
                           metrics=get_model_metrics())


@prediction_bp.route('/new', methods=['GET', 'POST'])
@login_required
@farmer_required
def new_prediction():
    batches = _get_farmer_batches()
    if not batches:
        flash('Please add a farm and an active batch first.', 'warning')
        return redirect(url_for('batch.add_batch'))

    if not models_available():
        flash('ML models are not trained yet. Please run the training script first. '
              'See ml_models/train_models.py', 'warning')

    if request.method == 'POST':
        batch_id = int(request.form.get('batch_id', 0))
        batch = PoultryBatch.query.get(batch_id)
        farm = PoultryFarm.query.get(batch.farm_id) if batch else None
        if not batch or not farm or farm.farmer_id != current_user.id:
            flash('Invalid batch selection.', 'danger')
            return render_template('predictions/form.html', batches=batches)

        def _safe_float(val):
            try:
                return float(val) if val and val.strip() else None
            except (ValueError, AttributeError):
                return None

        def _safe_int(val, default=0):
            try:
                return int(val) if val else default
            except (ValueError, TypeError):
                return default

        params = {
            'batch_id': batch_id,
            'farm_id': batch.farm_id,
            'poultry_type': batch.poultry_type,
            'number_of_birds': batch.number_of_birds,
            'bird_age_weeks': _safe_int(request.form.get('bird_age_weeks'), batch.bird_age_weeks),
            'body_temperature': _safe_float(request.form.get('body_temperature')) or 41.0,
            'feed_consumption_kg': _safe_float(request.form.get('feed_consumption_kg')) or 0,
            'water_consumption_litres': _safe_float(request.form.get('water_consumption_litres')) or 0,
            'bird_weight_kg': _safe_float(request.form.get('bird_weight_kg')) or 0,
            'mortality_count': _safe_int(request.form.get('mortality_count'), 0),
            'symptoms_input': request.form.get('symptoms', '').strip()
        }

        # Validate mortality
        if params['mortality_count'] > batch.number_of_birds:
            flash('Mortality count cannot exceed total number of birds in batch.', 'danger')
            return render_template('predictions/form.html', batches=batches, batch=batch)

        # Run ML prediction
        result = predict_disease(params)

        if result.get('error') and not result.get('models_available', True):
            # Models not available - save without predictions
            prediction = DiseasePrediction(
                batch_id=batch_id,
                farmer_id=current_user.id,
                bird_age_weeks=params['bird_age_weeks'],
                body_temperature=params['body_temperature'],
                feed_consumption_kg=params['feed_consumption_kg'],
                water_consumption_litres=params['water_consumption_litres'],
                bird_weight_kg=params['bird_weight_kg'],
                mortality_count=params['mortality_count'],
                symptoms_input=params['symptoms_input'],
                xgboost_prediction='Model not trained',
                decision_tree_prediction='Model not trained',
                final_prediction='Model not trained'
            )
            db.session.add(prediction)
            db.session.commit()
            flash('Models not trained yet. Record saved. Please train the models first.', 'warning')
            return redirect(url_for('prediction.prediction_history'))

        # Find matching disease in DB
        disease = Disease.query.filter(
            Disease.name.ilike(f'%{result.get("final_prediction", "")}%')
        ).first()

        prediction = DiseasePrediction(
            batch_id=batch_id,
            farmer_id=current_user.id,
            disease_id=disease.id if disease else None,
            bird_age_weeks=params['bird_age_weeks'],
            body_temperature=params['body_temperature'],
            feed_consumption_kg=params['feed_consumption_kg'],
            water_consumption_litres=params['water_consumption_litres'],
            bird_weight_kg=params['bird_weight_kg'],
            mortality_count=params['mortality_count'],
            symptoms_input=params['symptoms_input'],
            xgboost_prediction=result.get('xgboost_prediction'),
            xgboost_confidence=result.get('xgboost_confidence'),
            decision_tree_prediction=result.get('decision_tree_prediction'),
            decision_tree_confidence=result.get('decision_tree_confidence'),
            final_prediction=result.get('final_prediction'),
            prediction_date=datetime.utcnow()
        )
        db.session.add(prediction)
        db.session.commit()

        # Get recommendations
        recommendations = get_recommendations(result.get('final_prediction'))

        return render_template('predictions/result.html',
                               prediction=prediction,
                               result=result,
                               recommendations=recommendations,
                               batch=batch)

    # Pre-select batch if passed in query
    selected_batch_id = request.args.get('batch_id')
    selected_batch = None
    if selected_batch_id:
        selected_batch = PoultryBatch.query.get(int(selected_batch_id))

    return render_template('predictions/form.html',
                           batches=batches,
                           batch=selected_batch,
                           models_ready=models_available())


@prediction_bp.route('/<int:pred_id>')
@prediction_bp.route('/view/<int:pred_id>')
@login_required
def view_prediction(pred_id):
    pred = DiseasePrediction.query.get_or_404(pred_id)
    # Authorization
    if current_user.role != 'admin' and pred.farmer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('prediction.prediction_history'))
    batch = PoultryBatch.query.get(pred.batch_id)
    recommendations = get_recommendations(pred.final_prediction)
    return render_template('predictions/result.html',
                           prediction=pred,
                           result={
                               'xgboost_prediction': pred.xgboost_prediction,
                               'xgboost_confidence': pred.xgboost_confidence,
                               'decision_tree_prediction': pred.decision_tree_prediction,
                               'decision_tree_confidence': pred.decision_tree_confidence,
                               'final_prediction': pred.final_prediction,
                               'agreement': pred.xgboost_prediction == pred.decision_tree_prediction
                           },
                           recommendations=recommendations,
                           batch=batch)


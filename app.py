from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Template filters
    @app.template_filter('format_number')
    def format_number_filter(val):
        try:
            return f"{int(val):,}"
        except (ValueError, TypeError):
            return str(val) if val is not None else '0'

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.farmer_routes import farmer_bp
    from routes.farm_routes import farm_bp
    from routes.batch_routes import batch_bp
    from routes.health_routes import health_bp
    from routes.prediction_routes import prediction_bp
    from routes.vaccination_routes import vaccination_bp
    from routes.report_routes import report_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(farmer_bp, url_prefix='/farmer')
    app.register_blueprint(farm_bp, url_prefix='/farms')
    app.register_blueprint(batch_bp, url_prefix='/batches')
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(prediction_bp, url_prefix='/predictions')
    app.register_blueprint(vaccination_bp, url_prefix='/vaccinations')
    app.register_blueprint(report_bp, url_prefix='/reports')

    # Create tables
    with app.app_context():
        from models import user, farm, batch, health, disease, vaccination
        db.create_all()
        _seed_initial_data()

    return app


def _seed_initial_data():
    """Seed default admin and disease data if not present."""
    from models.user import Admin
    from models.disease import Disease
    from werkzeug.security import generate_password_hash

    # Default admin
    if not Admin.query.first():
        admin = Admin(
            username='admin',
            email='admin@poultry.com',
            password_hash=generate_password_hash('admin123'),
            full_name='System Administrator',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()

    # Seed disease reference data
    if not Disease.query.first():
        diseases = _get_disease_data()
        for d in diseases:
            db.session.add(Disease(**d))
        db.session.commit()


def _get_disease_data():
    return [
        {
            'name': 'Newcastle Disease',
            'description': 'A highly contagious viral disease affecting birds worldwide. Caused by avian paramyxovirus type 1 (APMV-1).',
            'symptoms': 'Respiratory distress, nervous signs (torticollis, paralysis), greenish diarrhea, sudden death, drop in egg production',
            'prevention': 'Regular vaccination, strict biosecurity, quarantine new birds, avoid contact with wild birds',
            'hygiene_recommendations': 'Disinfect equipment and housing regularly, control visitor access, clean water and feed systems',
            'biosecurity_measures': 'All-in all-out management, controlled access, vector control, secure feed storage',
            'isolation_guidance': 'Isolate affected birds immediately, notify veterinary authorities, do not move birds off premises',
            'veterinary_advice': 'Contact a licensed veterinarian immediately. This is a notifiable disease in many countries.',
            'severity': 'High'
        },
        {
            'name': 'Infectious Bursal Disease (Gumboro)',
            'description': 'Viral disease affecting young chickens (3–6 weeks old), targeting the bursa of Fabricius and suppressing the immune system.',
            'symptoms': 'Sudden onset of depression, watery whitish diarrhea, ruffled feathers, reluctance to move, high mortality in young birds',
            'prevention': 'Vaccination of breeders and chicks, strict biosecurity measures, avoid overcrowding',
            'hygiene_recommendations': 'Thorough cleaning and disinfection between flocks, all-in all-out management',
            'biosecurity_measures': 'Prevent exposure to contaminated fomites; virus is highly resistant in the environment',
            'isolation_guidance': 'Isolate affected flocks, limit farm access to essential personnel only',
            'veterinary_advice': 'Consult a veterinarian for supportive care and vaccination protocol review.',
            'severity': 'High'
        },
        {
            'name': 'Avian Influenza',
            'description': 'Highly contagious respiratory disease caused by influenza A viruses. HPAI strains can cause near 100% mortality.',
            'symptoms': 'Sudden death, respiratory distress, cyanosis of comb/wattles, swollen head/face, neurological signs, drop in egg production',
            'prevention': 'Vaccination (where approved), strict biosecurity, prevent contact with migratory wild birds, water sanitation',
            'hygiene_recommendations': 'Disinfection of all equipment, vehicles and personnel entering premises; use approved disinfectants',
            'biosecurity_measures': 'Bio-containment zones, control wild bird access, secure water sources, rodent control',
            'isolation_guidance': 'Immediate isolation and reporting to authorities; do not move birds. This is a zoonotic disease.',
            'veterinary_advice': 'Report to veterinary and public health authorities immediately. This is a notifiable disease with public health implications.',
            'severity': 'Critical'
        },
        {
            'name': 'Marek\'s Disease',
            'description': 'Lymphoproliferative disease caused by a herpesvirus, primarily affecting chickens aged 12–30 weeks.',
            'symptoms': 'Progressive leg or wing paralysis, weight loss, vision impairment, skin tumors, immunosuppression',
            'prevention': 'Vaccination of day-old chicks is highly effective; early vaccination is essential',
            'hygiene_recommendations': 'Maintain clean hatchery environment, reduce early chick stress',
            'biosecurity_measures': 'Vaccinate all chicks, buy from reputable disease-free sources, minimize environmental contamination',
            'isolation_guidance': 'Remove affected birds from the flock to prevent spread and suffering',
            'veterinary_advice': 'Work with a poultry veterinarian to establish a hatchery vaccination program.',
            'severity': 'Medium'
        },
        {
            'name': 'Coccidiosis',
            'description': 'Intestinal parasitic disease caused by Eimeria species. Very common in broilers and young birds.',
            'symptoms': 'Bloody diarrhea, pale comb, depression, poor feed conversion, weight loss, hunched posture',
            'prevention': 'Coccidiostats in feed, vaccination with live oocysts, good litter management, avoid overcrowding',
            'hygiene_recommendations': 'Keep litter dry and well-managed, avoid wet areas around drinkers, regular clean-out',
            'biosecurity_measures': 'Prevent contamination of feed and water with feces, control rodents and wild birds',
            'isolation_guidance': 'Severe cases should be separated; consult a vet for treatment options',
            'veterinary_advice': 'Consult a veterinarian for appropriate anticoccidial treatment and rotation strategy.',
            'severity': 'Medium'
        },
        {
            'name': 'Infectious Bronchitis',
            'description': 'Highly contagious viral respiratory disease of chickens caused by gammacoronavirus.',
            'symptoms': 'Coughing, sneezing, nasal discharge, reduced egg production, poor egg quality, watery eyes',
            'prevention': 'Vaccination, biosecurity, reduce stress, avoid overcrowding',
            'hygiene_recommendations': 'Good ventilation, avoid dust and ammonia buildup, clean and disinfect regularly',
            'biosecurity_measures': 'All-in all-out management, control movement of personnel and equipment',
            'isolation_guidance': 'Isolate coughing birds to slow spread within the flock',
            'veterinary_advice': 'Consult a veterinarian to identify the strain and recommend the appropriate vaccine.',
            'severity': 'Medium'
        },
        {
            'name': 'Fowl Cholera',
            'description': 'Bacterial disease caused by Pasteurella multocida, affecting chickens, turkeys, and other poultry.',
            'symptoms': 'Sudden death, greenish-yellow diarrhea, swollen wattles and sinuses, labored breathing, nasal discharge',
            'prevention': 'Vaccination, biosecurity, eliminate carrier birds, rodent control',
            'hygiene_recommendations': 'Remove dead birds promptly, disinfect premises, control insects and rodents',
            'biosecurity_measures': 'Prevent contact with wild birds and rodents, use separate equipment for each building',
            'isolation_guidance': 'Isolate sick birds immediately; remove and safely dispose of dead birds',
            'veterinary_advice': 'Veterinary-prescribed antibiotics may help reduce losses. Work with a vet for diagnosis and treatment.',
            'severity': 'High'
        },
        {
            'name': 'Salmonellosis',
            'description': 'Bacterial infection caused by Salmonella species. Important for food safety and human health.',
            'symptoms': 'Diarrhea, lethargy, reduced growth, dehydration, increased mortality in young birds',
            'prevention': 'Vaccination (Salmonella Typhimurium/Enteritidis), competitive exclusion, biosecurity, clean feed and water',
            'hygiene_recommendations': 'Strict hygiene in hatcheries and farms, monitor rodent activity, clean water systems regularly',
            'biosecurity_measures': 'All-in all-out management, test breeding flocks, control pests, monitor water quality',
            'isolation_guidance': 'Quarantine affected birds; this is a zoonotic disease requiring careful management',
            'veterinary_advice': 'Consult a veterinarian and food safety authority. Antibiotic use must be carefully managed to prevent resistance.',
            'severity': 'High'
        },
    ]


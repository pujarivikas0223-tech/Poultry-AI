"""
Recommendation service for disease prevention and management.
Based on the disease database entries.
"""
from models.disease import Disease


def get_recommendations(disease_name: str) -> dict:
    """
    Retrieve structured prevention recommendations for a predicted disease.
    Returns data from database if available, else returns a general advisory.
    """
    if not disease_name:
        return _general_advisory()

    disease = Disease.query.filter(
        Disease.name.ilike(f'%{disease_name}%')
    ).first()

    if disease:
        return {
            'disease_name': disease.name,
            'description': disease.description,
            'symptoms': disease.symptoms,
            'prevention': disease.prevention,
            'hygiene_recommendations': disease.hygiene_recommendations,
            'biosecurity_measures': disease.biosecurity_measures,
            'isolation_guidance': disease.isolation_guidance,
            'veterinary_advice': disease.veterinary_advice,
            'severity': disease.severity,
            'found_in_db': True
        }

    # Fallback: general advisory
    result = _general_advisory()
    result['disease_name'] = disease_name
    result['found_in_db'] = False
    return result


def _general_advisory() -> dict:
    return {
        'disease_name': 'Unknown / Needs Diagnosis',
        'description': (
            'The ML model has flagged potential health issues in this batch. '
            'A specific disease could not be confidently identified from the '
            'available parameters. Immediate veterinary consultation is recommended.'
        ),
        'symptoms': 'Review the symptoms observed in the flock carefully.',
        'prevention': (
            'Maintain strict biosecurity. Quarantine any sick birds. '
            'Review vaccination status immediately.'
        ),
        'hygiene_recommendations': (
            'Disinfect all equipment, water and feed systems. '
            'Remove and safely dispose of dead birds. Wash hands and change '
            'clothing between handling different birds.'
        ),
        'biosecurity_measures': (
            'Restrict access to the farm. '
            'Do not share equipment with neighbouring farms. '
            'Monitor all birds closely for new symptoms.'
        ),
        'isolation_guidance': (
            'Isolate visibly sick birds immediately. '
            'Set up a separate sick pen away from the main flock.'
        ),
        'veterinary_advice': (
            'Contact a licensed veterinarian immediately for a proper clinical '
            'examination and laboratory diagnosis. Do not administer medication '
            'without veterinary guidance.'
        ),
        'severity': 'Unknown',
        'found_in_db': False
    }


-- ============================================================
-- Poultry Disease Prevention & Vaccination Management System
-- Database: poultry_db
-- MySQL Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS poultry_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE poultry_db;

-- Admins
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    INDEX idx_admins_email (email)
) ENGINE=InnoDB;

-- Farmers
CREATE TABLE IF NOT EXISTS farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL UNIQUE,
    address TEXT,
    password_hash VARCHAR(255) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    INDEX idx_farmers_email (email),
    INDEX idx_farmers_phone (phone)
) ENGINE=InnoDB;

-- Poultry Farms
CREATE TABLE IF NOT EXISTS poultry_farms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    farm_name VARCHAR(150) NOT NULL,
    location VARCHAR(200),
    address TEXT,
    farm_size VARCHAR(50),
    total_capacity INT DEFAULT 0,
    contact_number VARCHAR(20),
    description TEXT,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    INDEX idx_farms_farmer (farmer_id)
) ENGINE=InnoDB;

-- Poultry Batches
CREATE TABLE IF NOT EXISTS poultry_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farm_id INT NOT NULL,
    batch_name VARCHAR(100) NOT NULL,
    breed_name VARCHAR(100) NOT NULL,
    poultry_type VARCHAR(50) NOT NULL DEFAULT 'Broiler',
    number_of_birds INT NOT NULL DEFAULT 0,
    bird_age_weeks INT DEFAULT 0,
    arrival_date DATE NOT NULL,
    expected_harvest_date DATE,
    source VARCHAR(150),
    purchase_price_per_bird FLOAT DEFAULT 0.0,
    batch_status VARCHAR(30) DEFAULT 'Active',
    notes TEXT,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (farm_id) REFERENCES poultry_farms(id) ON DELETE CASCADE,
    INDEX idx_batches_farm (farm_id)
) ENGINE=InnoDB;

-- Poultry Breeds Reference
CREATE TABLE IF NOT EXISTS poultry_breeds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    breed_name VARCHAR(100) NOT NULL UNIQUE,
    poultry_type VARCHAR(50),
    description TEXT,
    avg_weight_kg FLOAT,
    egg_production VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Health Records
CREATE TABLE IF NOT EXISTS poultry_health_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    farm_id INT NOT NULL,
    number_of_birds INT NOT NULL,
    bird_age_weeks INT NOT NULL,
    body_temperature FLOAT,
    feed_consumption_kg FLOAT,
    water_consumption_litres FLOAT,
    bird_weight_kg FLOAT,
    mortality_count INT DEFAULT 0,
    symptoms TEXT,
    health_condition VARCHAR(50),
    record_date DATE NOT NULL,
    notes TEXT,
    recorded_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES poultry_batches(id) ON DELETE CASCADE,
    FOREIGN KEY (farm_id) REFERENCES poultry_farms(id) ON DELETE CASCADE,
    FOREIGN KEY (recorded_by) REFERENCES farmers(id) ON DELETE SET NULL,
    INDEX idx_health_batch (batch_id),
    INDEX idx_health_farm (farm_id),
    INDEX idx_health_date (record_date)
) ENGINE=InnoDB;

-- Diseases Reference
CREATE TABLE IF NOT EXISTS diseases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    symptoms TEXT,
    prevention TEXT,
    hygiene_recommendations TEXT,
    biosecurity_measures TEXT,
    isolation_guidance TEXT,
    veterinary_advice TEXT,
    severity VARCHAR(20) DEFAULT 'Medium',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_diseases_name (name)
) ENGINE=InnoDB;

-- Disease Predictions (ML Results)
CREATE TABLE IF NOT EXISTS disease_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    farmer_id INT NOT NULL,
    disease_id INT,
    bird_age_weeks INT,
    body_temperature FLOAT,
    feed_consumption_kg FLOAT,
    water_consumption_litres FLOAT,
    bird_weight_kg FLOAT,
    mortality_count INT DEFAULT 0,
    symptoms_input TEXT,
    xgboost_prediction VARCHAR(150),
    xgboost_confidence FLOAT,
    decision_tree_prediction VARCHAR(150),
    decision_tree_confidence FLOAT,
    final_prediction VARCHAR(150),
    prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_confirmed TINYINT(1) DEFAULT 0,
    veterinary_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES poultry_batches(id) ON DELETE CASCADE,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    FOREIGN KEY (disease_id) REFERENCES diseases(id) ON DELETE SET NULL,
    INDEX idx_predictions_farmer (farmer_id),
    INDEX idx_predictions_batch (batch_id)
) ENGINE=InnoDB;

-- Vaccination Records
CREATE TABLE IF NOT EXISTS vaccination_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    farmer_id INT NOT NULL,
    vaccine_name VARCHAR(150) NOT NULL,
    vaccination_date DATE NOT NULL,
    next_vaccination_date DATE,
    dosage VARCHAR(100),
    route VARCHAR(50),
    batch_lot_number VARCHAR(100),
    administered_by VARCHAR(150),
    status VARCHAR(30) DEFAULT 'Completed',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES poultry_batches(id) ON DELETE CASCADE,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    INDEX idx_vacc_batch (batch_id),
    INDEX idx_vacc_farmer (farmer_id),
    INDEX idx_vacc_date (vaccination_date)
) ENGINE=InnoDB;

-- Vaccination Schedules (Reference data)
CREATE TABLE IF NOT EXISTS vaccination_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    poultry_type VARCHAR(50) NOT NULL,
    vaccine_name VARCHAR(150) NOT NULL,
    recommended_age_weeks INT NOT NULL,
    description TEXT,
    route VARCHAR(50),
    notes TEXT,
    is_mandatory TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_schedules_type (poultry_type)
) ENGINE=InnoDB;


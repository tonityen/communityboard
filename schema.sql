CREATE DATABASE IF NOT EXISTS communityboard CHARACTER SET utf8mb4;
USE communityboard;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('resident', 'admin') NOT NULL DEFAULT 'resident',
    is_verified TINYINT(1) NOT NULL DEFAULT 0,
    photo VARCHAR(255) NULL,
    username VARCHAR(20) NULL UNIQUE,
    contact_number VARCHAR(11) NULL,
    purok VARCHAR(60) NULL,
    status ENUM('active', 'disabled') NOT NULL DEFAULT 'active',
    failed_attempts INT NOT NULL DEFAULT 0,
    locked_until DATETIME NULL,
    verification_code_hash CHAR(64) NULL,
    verification_code_expires_at DATETIME NULL,
    verification_code_sent_at DATETIME NULL,
    verification_attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL,
    image VARCHAR(255) NULL,
    category VARCHAR(40) NOT NULL DEFAULT 'General',
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    event_date DATE NOT NULL,
    location VARCHAR(150),
    image VARCHAR(255) NULL,
    category VARCHAR(40) NOT NULL DEFAULT 'Community',
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(60) NOT NULL,
    subject VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('open', 'in_progress', 'resolved') NOT NULL DEFAULT 'open',
    incident_location VARCHAR(150) NULL,
    incident_date DATE NULL,
    resolution_note TEXT NULL,
    updated_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS ticket_endorsements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_ticket_endorsement (ticket_id, user_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

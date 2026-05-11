import os
from datetime import datetime

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_DATABASE', 'hotspot_db'),
}


def get_db_connection():
    """Open a new connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
        )
        return connection
    except Error as err:
        print('Error connecting to MySQL:', err)
        return None


def initialize_database():
    """Create tables if they do not already exist."""
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError('Database connection failed. Check MySQL settings.')

    cursor = connection.cursor()

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            phone_number VARCHAR(50) UNIQUE,
            mac_address VARCHAR(100)
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS packages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            price DECIMAL(10, 2),
            duration_minutes INT
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            amount DECIMAL(10, 2),
            package_id INT,
            date DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (package_id) REFERENCES packages(id)
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            package_id INT,
            login_time DATETIME,
            logout_time DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (package_id) REFERENCES packages(id)
        )
        '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS vouchers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id VARCHAR(100) UNIQUE,
            user_id INT,
            package_id INT,
            status ENUM('active', 'inactive') DEFAULT 'inactive',
            created_at DATETIME,
            expires_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (package_id) REFERENCES packages(id)
        )
        '''
    )

    connection.commit()
    cursor.close()
    connection.close()


def insert_sample_packages():
    """Insert sample packages if they do not already exist."""
    connection = get_db_connection()
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute('SELECT name FROM packages')
    existing_names = {row[0] for row in cursor.fetchall()}

    packages = [
        ('6 hours Wetase', 500.00, 360),
        ('12 Hours', 700.00, 720),
        ('26 hours', 1000.00, 1560),
        ('3 days', 2500.00, 4320),
        ('Week', 5000.00, 10080),
        ('14 Days', 8500.00, 20160),
        ('Premium for Tv', 15000.00, 43200),
        ('Month', 19000.00, 43200),
    ]

    missing_packages = [pkg for pkg in packages if pkg[0] not in existing_names]
    if missing_packages:
        cursor.executemany(
            'INSERT INTO packages (name, price, duration_minutes) VALUES (%s, %s, %s)',
            missing_packages,
        )
        connection.commit()

    cursor.close()
    connection.close()


def insert_sample_vouchers():
    """Insert sample vouchers for testing if vouchers table is empty."""
    connection = get_db_connection()
    if connection is None:
        return

    cursor = connection.cursor()
    cursor.execute('SELECT COUNT(*) FROM vouchers')
    voucher_count = cursor.fetchone()[0]

    if voucher_count == 0:
        # Create a test user if not exists
        cursor.execute('SELECT id FROM users LIMIT 1')
        user_id = cursor.fetchone()
        if user_id is None:
            cursor.execute(
                'INSERT INTO users (phone_number, mac_address) VALUES (%s, %s)',
                ('test_user', None),
            )
            connection.commit()
            user_id = cursor.lastrowid
        else:
            user_id = user_id[0]

        # Insert sample vouchers
        sample_vouchers = [
            ('TXN123456', user_id, 1, 'active', get_current_time(), datetime.utcnow() + timedelta(days=30)),
            ('TXN789012', user_id, 5, 'active', get_current_time(), datetime.utcnow() + timedelta(days=30)),
            ('TXN345678', user_id, 8, 'inactive', get_current_time(), datetime.utcnow() + timedelta(days=30)),
        ]
        cursor.executemany(
            'INSERT INTO vouchers (transaction_id, user_id, package_id, status, created_at, expires_at) VALUES (%s, %s, %s, %s, %s, %s)',
            sample_vouchers,
        )
        connection.commit()

    cursor.close()
    connection.close()


def get_current_time():
    return datetime.utcnow()

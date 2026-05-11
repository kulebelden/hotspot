from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from db import get_db_connection, initialize_database, insert_sample_packages, insert_sample_vouchers, get_current_time

auth_bp = Blueprint('auth', __name__)

# Initialize database tables and sample packages when the module is first imported.
initialize_database()
insert_sample_packages()
insert_sample_vouchers()


def find_user_by_phone(phone_number):
    connection = get_db_connection()
    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE phone_number = %s', (phone_number,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user


def create_user(phone_number, mac_address=None):
    connection = get_db_connection()
    if connection is None:
        return None

    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO users (phone_number, mac_address) VALUES (%s, %s)',
        (phone_number, mac_address),
    )
    connection.commit()
    user_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return {
        'id': user_id,
        'phone_number': phone_number,
        'mac_address': mac_address,
    }


def get_active_session(user_id):
    connection = get_db_connection()
    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        '''
        SELECT s.*, p.duration_minutes
        FROM sessions s
        LEFT JOIN packages p ON s.package_id = p.id
        WHERE s.user_id = %s
        ORDER BY s.login_time DESC
        LIMIT 1
        ''',
        (user_id,),
    )
    session = cursor.fetchone()
    cursor.close()
    connection.close()
    return session


def user_has_active_package(user_id):
    session = get_active_session(user_id)
    if session is None:
        return False

    if session['logout_time'] is None:
        return True

    now = get_current_time()
    return session['logout_time'] > now


def get_package_by_id(package_id):
    connection = get_db_connection()
    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM packages WHERE id = %s', (package_id,))
    package = cursor.fetchone()
    cursor.close()
    connection.close()
    return package


def create_payment(user_id, amount, package_id):
    connection = get_db_connection()
    if connection is None:
        return None

    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO payments (user_id, amount, package_id, date) VALUES (%s, %s, %s, %s)',
        (user_id, amount, package_id, get_current_time()),
    )
    connection.commit()
    payment_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return payment_id


def activate_package(user_id, package_id):
    package = get_package_by_id(package_id)
    if package is None:
        return None

    connection = get_db_connection()
    if connection is None:
        return None

    login_time = get_current_time()
    logout_time = login_time + timedelta(minutes=package['duration_minutes'])

    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO sessions (user_id, package_id, login_time, logout_time) VALUES (%s, %s, %s, %s)',
        (user_id, package_id, login_time, logout_time),
    )
    connection.commit()
    session_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return session_id


auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    phone_number = data.get('phone_number')
    voucher_code = data.get('voucher_code')
    mac_address = data.get('mac_address')

    if not phone_number and not voucher_code:
        return jsonify({'error': 'Please provide phone_number or voucher_code.'}), 400

    # Simpler authentication: use phone number or voucher code as the user key.
    if voucher_code:
        phone_number = voucher_code

    user = find_user_by_phone(phone_number)
    if user is None:
        user = create_user(phone_number, mac_address)

    if user_has_active_package(user['id']):
        return jsonify({'message': 'Access granted. Active package found.', 'user': user}), 200

    return jsonify({
        'message': 'No active package. Please pay to activate a package.',
        'user': user,
        'next': '/pay'
    }), 200


auth_bp.route('/pay', methods=['POST'])
def pay():
    data = request.json or {}
    phone_number = data.get('phone_number')
    voucher_code = data.get('voucher_code')
    package_id = data.get('package_id')

    if not package_id:
        return jsonify({'error': 'Please provide package_id.'}), 400

    if not phone_number and not voucher_code:
        return jsonify({'error': 'Please provide phone_number or voucher_code.'}), 400

    if voucher_code:
        phone_number = voucher_code

    user = find_user_by_phone(phone_number)
    if user is None:
        return jsonify({'error': 'User not found. Please login first.'}), 404

    package = get_package_by_id(package_id)
    if package is None:
        return jsonify({'error': 'Package not found.'}), 404

    # Simulate mobile money payment by simply storing a payment record.
    payment_id = create_payment(user['id'], package['price'], package_id)
    session_id = activate_package(user['id'], package_id)

    return jsonify({
        'message': 'Payment simulated and package activated.',
        'payment_id': payment_id,
        'session_id': session_id,
        'package': package
    }), 200


auth_bp.route('/status', methods=['GET'])
def status():
    phone_number = request.args.get('phone_number')
    voucher_code = request.args.get('voucher_code')

    if not phone_number and not voucher_code:
        return jsonify({'error': 'Please provide phone_number or voucher_code.'}), 400

    if voucher_code:
        phone_number = voucher_code

    user = find_user_by_phone(phone_number)
    if user is None:
        return jsonify({'error': 'User not found.'}), 404

    active = user_has_active_package(user['id'])
    return jsonify({
        'user': user,
        'active_package': active
    }), 200


@auth_bp.route('/search-voucher', methods=['POST'])
def search_voucher():
    """Search for a voucher by transaction ID and activate if found and active."""
    data = request.json or {}
    transaction_id = data.get('transaction_id', '').strip()

    if not transaction_id or len(transaction_id) < 6:
        return jsonify({'error': 'Transaction ID must be at least 6 characters.'}), 400

    connection = get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed.'}), 500

    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM vouchers WHERE transaction_id = %s AND status = "active"',
        (transaction_id,),
    )
    voucher = cursor.fetchone()
    cursor.close()
    connection.close()

    if voucher is None:
        return jsonify({'error': 'No voucher found for this transaction ID. Please check your transaction ID and try again.'}), 404

    if voucher['expires_at'] and get_current_time() > voucher['expires_at']:
        return jsonify({'error': 'This voucher has expired.'}), 400

    # Fetch user by ID for the voucher.
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE id = %s', (voucher['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user is None:
        return jsonify({'error': 'User not found for this voucher.'}), 404

    session_id = activate_package(user['id'], voucher['package_id'])
    return jsonify({
        'message': 'Voucher found and activated!',
        'session_id': session_id,
        'user': user,
    }), 200

from flask import Blueprint, jsonify
from db import get_db_connection

admin_bp = Blueprint('admin', __name__)


def query_earnings(interval):
    connection = get_db_connection()
    if connection is None:
        return 0.0

    cursor = connection.cursor()

    if interval not in ('1 DAY', '7 DAY', '30 DAY'):
        interval = '1 DAY'

    query = f"SELECT COALESCE(SUM(amount), 0) FROM payments WHERE date >= NOW() - INTERVAL {interval}"
    cursor.execute(query)
    total = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return float(total)


@admin_bp.route('/admin/stats', methods=['GET'])
def stats():
    earnings = {
        'daily': query_earnings('1 DAY'),
        'weekly': query_earnings('7 DAY'),
        'monthly': query_earnings('30 DAY'),
    }
    return jsonify({'earnings': earnings}), 200

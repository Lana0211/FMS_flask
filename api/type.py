# api/type.py
import pyodbc
from flask import Blueprint, current_app, jsonify, request

type_blueprint = Blueprint('type', __name__)

def get_db_connection():
    return pyodbc.connect(current_app.config['DB_CONNECTION_STRING'], autocommit=True)

@type_blueprint.route('/types', methods=['GET'])
def get_types():
    type_id = request.args.get('type_id', default=None)
    type = request.args.get('type')  # 'income' 或 'expenditure'

    conn = get_db_connection()
    cursor = conn.cursor()

    if type == 'income':
        table_name = 'IncomeType'
    elif type == 'expenditure':
        table_name = 'ExpenditureType'
    else:
        return jsonify({'message': 'Invalid type category specified.'}), 400

    if type_id:
        cursor.execute(f'SELECT TypeName FROM {table_name} WHERE {table_name}_id = ?', (type_id,))
        row = cursor.fetchone()
        if row:
            result = {'type_id': type_id, 'name': row[0]}
        else:
            return jsonify({'message': 'Type ID not found.'}), 404
    else:
        cursor.execute(f'SELECT {table_name}_id, TypeName FROM {table_name}')
        rows = cursor.fetchall()
        result = [{'type_id': row[0], 'name': row[1]} for row in rows]

    cursor.close()
    conn.close()

    return jsonify(result), 200

# api/type.py
import pyodbc
from flask import Blueprint, current_app, jsonify, request

type_blueprint = Blueprint('type', __name__)

def get_db_connection():
    return pyodbc.connect(current_app.config['DB_CONNECTION_STRING'], autocommit=True)

@type_blueprint.route('/api/types', methods=['GET'])
def get_types():
    type_requested = request.args.get('type')  # 獲取類型：收入/支出
    conn = get_db_connection()  # 获取数据库连接
    cursor = conn.cursor()

    if type_requested == 'income':
        # 查询所有收入类型
        cursor.execute('SELECT * FROM IncomeType ORDER BY IncomeType_id ASC')
    elif type_requested == 'expenditure':
        # 查询所有支出类型
        cursor.execute('SELECT * FROM ExpenditureType ORDER BY ExpenditureType_id ASC')
    else:
        return jsonify({'message': 'Invalid type specified.'}), 400
    types = cursor.fetchall()
    types_list = [{'id': row[0], 'name': row[1]} for row in types]

    cursor.close()
    conn.close()

    return jsonify(types_list)

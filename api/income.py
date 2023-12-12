# api/income.py
from datetime import datetime

import pyodbc
from flask import Blueprint, current_app, jsonify, request

income_blueprint = Blueprint('income', __name__)

def get_db_connection():
    return pyodbc.connect(current_app.config['DB_CONNECTION_STRING'], autocommit=True)

@income_blueprint.route('/incomes', methods=['POST'])
def create_income():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Income (User_id, Amount, IncomeType_id, IncomeDate)
        VALUES (?, ?, ?, ?)
    ''', data['user_id'], data['amount'], data['income_type'], data['income_date'])
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Income created successfully.'}), 201

@income_blueprint.route('/incomes/<int:income_id>', methods=['PUT'])
def update_income(income_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    # 查收入類型的名字
    cursor.execute('''
        SELECT it.TypeName 
        FROM Income i 
        JOIN IncomeType it ON i.IncomeType_id = it.IncomeType_id 
        WHERE i.Income_id = ?
    ''', income_id)
    result = cursor.fetchone()

    if result and result[0] == '股票':
        cursor.close()
        conn.close()
        return jsonify({'message': 'Cannot update stock income.'}), 400

    cursor.execute('''
        UPDATE Income
        SET Amount = ?, IncomeType_id = ?, IncomeDate = ?
        WHERE Income_id = ?
    ''', data['amount'], data['income_type'], data['income_date'], income_id)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Income updated successfully.'})

@income_blueprint.route('/incomes/<int:income_id>', methods=['DELETE'])
def delete_income(income_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 查收入類型的名字
    cursor.execute('''
        SELECT it.TypeName 
        FROM Income i 
        JOIN IncomeType it ON i.IncomeType_id = it.IncomeType_id 
        WHERE i.Income_id = ?
    ''', income_id)
    result = cursor.fetchone()

    if result and result[0] == '股票':
        cursor.close()
        conn.close()
        return jsonify({'message': 'Cannot delete stock income.'}), 400

    # 如果不是股票收入，执行删除操作
    cursor.execute('DELETE FROM Income WHERE Income_id = ?', income_id)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Income deleted successfully.'})


@income_blueprint.route('/incomes', methods=['GET'])
def get_incomes():
    year = request.args.get('year', default=str(datetime.now().year))
    month = request.args.get('month', default=str(datetime.now().month).zfill(2))
    income_type = request.args.get('income_type')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT i.Income_id, i.User_id, i.Amount, it.TypeName, i.IncomeDate
        FROM Income i
        JOIN IncomeType it ON i.IncomeType_id = it.IncomeType_id
        WHERE YEAR(i.IncomeDate) = ? AND MONTH(i.IncomeDate) = ?
        ORDER BY i.IncomeDate DESC
    '''

    total_amount_query = '''
        SELECT SUM(Amount)
        FROM Income
        WHERE YEAR(IncomeDate) = ? AND MONTH(IncomeDate) = ? 
    '''
    query_params = [year, month]
    
    if income_type:
        query += ' AND IncomeType_id = ?'
        total_amount_query += ' AND IncomeType_id = ?'
        query_params.append(income_type)
    
    cursor.execute(query, query_params)
    
    incomes = cursor.fetchall()
    incomes_list = [{'income_id': row[0], 'user_id': row[1], 'amount': row[2], 'type': row[3], 'date': row[4].strftime('%Y-%m-%d')} for row in incomes]
    
    # 計算total
    cursor.execute(total_amount_query, query_params)
    total_amount = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()

    return jsonify({
        'incomes': incomes_list,
        'total_amount': total_amount
    })


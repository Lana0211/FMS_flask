# api/expenditure.py
from datetime import datetime

import pyodbc
from flask import Blueprint, current_app, jsonify, request

expenditure_blueprint = Blueprint('expenditure', __name__)

def get_db_connection():
    return pyodbc.connect(current_app.config['DB_CONNECTION_STRING'], autocommit=True)

@expenditure_blueprint.route('/expenditures', methods=['POST'])
def create_expenditure():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenditure (User_id, Amount, ExpenditureType_id, expenditureDate)
        VALUES (?, ?, ?, ?)
    ''', data['user_id'], data['amount'], data['expenditure_type'], data['expenditure_date'])
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Expenditure created successfully.'}), 201

@expenditure_blueprint.route('/expenditures/<int:expenditure_id>', methods=['PUT'])
def update_expenditure(expenditure_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    # 查支出類型的名字
    cursor.execute('''
        SELECT et.TypeName 
        FROM expenditure e 
        JOIN expenditureType et ON e.ExpenditureType_id = et.expenditureType_id 
        WHERE e.expenditure_id = ?
    ''', expenditure_id)
    result = cursor.fetchone()

    if result and result[0] == '股票':
        cursor.close()
        conn.close()
        return jsonify({'message': 'Cannot update stock expenditure.'}), 400

    # 如果不是股票支出，执行更新操作
    cursor.execute('''
        UPDATE expenditure
        SET Amount = ?, ExpenditureType_id = ?, expenditureDate = ?
        WHERE expenditure_id = ?
    ''', data['amount'], data['expenditure_type'], data['expenditure_date'], expenditure_id)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Expenditure updated successfully.'})

@expenditure_blueprint.route('/expenditures/<int:expenditure_id>', methods=['DELETE'])
def delete_expenditure(expenditure_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 查支出類型的名字
    cursor.execute('''
        SELECT et.TypeName 
        FROM Expenditure e 
        JOIN ExpenditureType et ON e.ExpenditureType_id = et.ExpenditureType_id 
        WHERE e.Expenditure_id = ?
    ''', expenditure_id)
    result = cursor.fetchone()

    if result and result[0] == '股票':
        cursor.close()
        conn.close()
        return jsonify({'message': 'Cannot delete stock expenditure.'}), 400

    # 如果不是股票支出，执行删除操作
    cursor.execute('DELETE FROM Expenditure WHERE Expenditure_id = ?', expenditure_id)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Expenditure deleted successfully.'})


@expenditure_blueprint.route('/expenditures', methods=['GET'])
def get_expenditure():
    year = request.args.get('year', default=str(datetime.now().year))
    month = request.args.get('month', default=str(datetime.now().month).zfill(2))
    expenditure_type = request.args.get('expenditure_type')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT Expenditure_id, User_id, Amount, ExpenditureType_id, ExpenditureDate
        FROM Expenditure
        WHERE YEAR(ExpenditureDate) = ? AND MONTH(ExpenditureDate) = ?
        ORDER BY ExpenditureDate DESC
    '''
    total_amount_query = '''
        SELECT SUM(Amount)
        FROM Expenditure
        WHERE YEAR(ExpenditureDate) = ? AND MONTH(ExpenditureDate) = ?
    '''
    query_params = [year, month]
    
    if expenditure_type:
        query += ' AND ExpenditureType_id = ?'
        total_amount_query += ' AND ExpenditureType_id = ?'
        query_params.append(expenditure_type)
    
    cursor.execute(query, query_params)
    
    expenditure = cursor.fetchall()
    expenditure_list = [{'expenditure_id': row[0], 'user_id': row[1], 'amount': row[2], 'expenditure_type': row[3], 'expenditure_date': row[4].strftime('%Y-%m-%d')} for row in expenditure]
    
    # 計算total
    cursor.execute(total_amount_query, query_params)
    total_amount = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return jsonify({
        'expenditure': expenditure_list,
        'total_amount': total_amount
    })


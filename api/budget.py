# api/budget.py
import pyodbc
from flask import Blueprint, current_app, jsonify, request

budget_blueprint = Blueprint('budget', __name__)

def get_db_connection():
    return pyodbc.connect(current_app.config['DB_CONNECTION_STRING'], autocommit=True)

@budget_blueprint.route('/budgets', methods=['POST'])
def create_budget():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    # 新增預算
    cursor.execute('''
        INSERT INTO Budget (User_id, Amount, ExpenditureType_id, StartDate, EndDate)
        VALUES (?, ?, ?, ?, ?)
    ''', data['user_id'], data['amount'], data['expenditure_type'], data['start_date'], data['end_date'])

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Budget created successfully.'}), 201

@budget_blueprint.route('/budgets/<int:budget_id>', methods=['PUT'])
def update_budget(budget_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    # 更新預算
    cursor.execute('''
        UPDATE Budget
        SET Amount = ?, ExpenditureType_id = ?, StartDate = ?, EndDate = ?
        WHERE Budget_id = ?
    ''', data['amount'], data['expenditure_type'], data['start_date'], data['end_date'], budget_id)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Budget updated successfully.'})

@budget_blueprint.route('/budgets/<int:budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 刪除預算
    cursor.execute('DELETE FROM Budget WHERE Budget_id = ?', budget_id)

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Budget deleted successfully.'})

@budget_blueprint.route('/budgets', methods=['GET'])
def get_budgets():
    year = request.args.get('year')
    month = request.args.get('month')
    expenditure_type = request.args.get('expenditure_type')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取在指定的开始和结束日期区间内的预算
    budget_query = '''
        SELECT Budget_id, User_id, Amount, ExpenditureType_id, StartDate, EndDate
        FROM Budget
        WHERE (YEAR(StartDate) = ? AND MONTH(StartDate) = ?) OR 
            (YEAR(EndDate) = ? AND MONTH(EndDate) = ?)
    '''
    budget_query_params = [year, month, year, month]

    if expenditure_type:
        budget_query += ' AND ExpenditureType_id = ?'
        budget_query_params.append(expenditure_type)

    cursor.execute(budget_query, budget_query_params)
    budgets = cursor.fetchall()
    budgets_list = [{'budget_id': row[0], 'user_id': row[1], 'amount': row[2], 'expenditure_type': row[3], 'start_date': row[4].strftime('%Y-%m-%d'), 'end_date': row[5].strftime('%Y-%m-%d')} for row in budgets]

    # 计算所有预算的支出总额
    total_amount = 0
    for budget in budgets_list:
        expenditure_query = '''
            SELECT SUM(Amount)
            FROM Expenditure
            WHERE ExpenditureType_id = ? AND ExpenditureDate BETWEEN ? AND ?
        '''
        cursor.execute(expenditure_query, (budget['expenditure_type'], budget['start_date'], budget['end_date']))
        expenditure_amount = cursor.fetchone()[0] or 0
        total_amount += expenditure_amount

    cursor.close()
    conn.close()

    return jsonify({
        'budgets': budgets_list,
        'total_amount': total_amount
    })



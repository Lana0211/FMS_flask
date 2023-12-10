# api/budget.py
from datetime import datetime

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

    # 檢查是否已經存在具有相同年月和類型的預算
    year, month, *_ = data['budget_date'].split('-')
    check_query = '''
        SELECT COUNT(*)
        FROM Budget
        WHERE User_id = ? AND ExpenditureType_id = ? AND 
            YEAR(BudgetDate) = ? AND MONTH(BudgetDate) = ?
    '''
    cursor.execute(check_query, (data['user_id'], data['expenditure_type'], year, month))
    if cursor.fetchone()[0] > 0:
        cursor.close()
        conn.close()
        return jsonify({'message': 'A budget for the specified month and type already exists.'}), 400

    # 計算剩餘預算
    expenditure_query = '''
        SELECT SUM(Amount)
        FROM Expenditure
        WHERE User_id = ? AND ExpenditureType_id = ? AND 
            YEAR(ExpenditureDate) = ? AND MONTH(ExpenditureDate) = ?
    '''
    cursor.execute(expenditure_query, (data['user_id'], data['expenditure_type'], year, month))
    total_expenditure = cursor.fetchone()[0] or 0
    remaining_budget = data['amount'] - total_expenditure

    # 新增預算
    cursor.execute('''
        INSERT INTO Budget (User_id, Amount, ExpenditureType_id, BudgetDate, RemainingBudget)
        VALUES (?, ?, ?, ?, ?)
    ''', data['user_id'], data['amount'], data['expenditure_type'], data['budget_date'], remaining_budget)

    conn.commit()
    cursor.close()
    conn.close()

    # 如果剩餘預算為負數
    if remaining_budget < 0: 
        return jsonify({'message': 'Budget created successfully.But remaining budget would be negative.'}), 201

    return jsonify({'message': 'Budget created successfully.'}), 201

@budget_blueprint.route('/budgets/<int:budget_id>', methods=['PUT'])
def update_budget(budget_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    # 原本預算
    cursor.execute('''
        SELECT Amount FROM Budget WHERE Budget_id = ?
    ''', (budget_id,))
    old_amount = cursor.fetchone()[0]

    # 計算剩餘預算的變化值
    budget_difference = data['amount'] - old_amount

    # 更新預算
    cursor.execute('''
        UPDATE Budget
        SET Amount = ?, ExpenditureType_id = ?, BudgetDate = ?, RemainingBudget = RemainingBudget + ?
        WHERE Budget_id = ?
    ''', (data['amount'], data['expenditure_type'], data['budget_date'], budget_difference, budget_id))

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
    year = request.args.get('year', default=str(datetime.now().year))
    month = request.args.get('month', default=str(datetime.now().month).zfill(2))
    expenditure_type = request.args.get('expenditure_type')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取在指定的日期区间内的预算
    budget_query = '''
        SELECT Budget_id, User_id, Amount, ExpenditureType_id, BudgetDate, RemainingBudget
        FROM Budget
        WHERE YEAR(BudgetDate) = ? AND MONTH(BudgetDate) = ?
        ORDER BY RemainingBudget DESC
    '''
    budget_query_params = [year, month]

    if expenditure_type:
        budget_query += ' AND ExpenditureType_id = ?'
        budget_query_params.append(expenditure_type)

    cursor.execute(budget_query, budget_query_params)
    budgets = cursor.fetchall()
    budgets_list = [{'budget_id': row[0], 'user_id': row[1], 'amount': row[2], 'expenditure_type': row[3], 'budget_date': row[4].strftime('%Y-%m-%d'), 'remaining_budget': row[5]} for row in budgets]

    cursor.close()
    conn.close()

    return jsonify(budgets_list), 200

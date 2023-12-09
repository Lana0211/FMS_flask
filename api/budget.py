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
        INSERT INTO Budget (User_id, Amount, ExpenditureType_id, BudgetDate)
        VALUES (?, ?, ?, ?)
    ''', data['user_id'], data['amount'], data['expenditure_type'], data['budget_date'])

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
        SET Amount = ?, ExpenditureType_id = ?, BudgetDate = ?
        WHERE Budget_id = ?
    ''', data['amount'], data['expenditure_type'], data['budget_date'], budget_id)

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
    
    # 获取在指定的日期区间内的预算
    budget_query = '''
        SELECT Budget_id, User_id, Amount, ExpenditureType_id, BudgetDate
        FROM Budget
        WHERE YEAR(BudgetDate) = ? AND MONTH(BudgetDate) = ?
    '''
    budget_query_params = [year, month]

    if expenditure_type:
        budget_query += ' AND ExpenditureType_id = ?'
        budget_query_params.append(expenditure_type)

    cursor.execute(budget_query, budget_query_params)
    budgets = cursor.fetchall()

    budgets_list = []
    for row in budgets:
        budget_id, user_id, amount, exp_type_id, budget_date = row
        # 对每一笔预算计算同年同月同类型的支出总额
        expenditure_query = '''
            SELECT SUM(Amount)
            FROM Expenditure
            WHERE ExpenditureType_id = ? AND YEAR(ExpenditureDate) = ? AND MONTH(ExpenditureDate) = ?
        '''
        cursor.execute(expenditure_query, (exp_type_id, year, month))
        total_expenditure = cursor.fetchone()[0] or 0

        budgets_list.append({
            'budget_id': budget_id, 
            'user_id': user_id, 
            'amount': amount, 
            'expenditure_type': exp_type_id, 
            'budget_date': budget_date.strftime('%Y-%m'), 
            'total_expenditure': total_expenditure
        })

    cursor.close()
    conn.close()

    return jsonify(budgets_list)

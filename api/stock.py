from flask import Blueprint, request, jsonify, current_app
from apscheduler.schedulers.background import BackgroundScheduler
import pyodbc
import twstock
from datetime import datetime

stock_blueprint = Blueprint('stock', __name__)

def get_db_connection():
    return pyodbc.connect(current_app.config['DB_CONNECTION_STRING'], autocommit=True)

def get_current_stock_price(stock_code):
    stock = twstock.Stock(stock_code)
    latest_data = stock.fetch()  # 获取最近的股票数据
    if latest_data:
        # 获取最新一天的收盘价作为当前价格
        return latest_data[-1].close
    return None

@stock_blueprint.route('/transactions', methods=['POST'])
def add_stock_transaction():
    # 检查请求数据是否存在
    if not request.data:
        return jsonify({'error': 'Empty request body'}), 400

    # 尝试解析 JSON 数据
    try:
        data = request.json
    except Exception as e:
        return jsonify({'error': 'Invalid JSON', 'message': str(e)}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 插入 Transactions 表
            cursor.execute("INSERT INTO Transactions (User_id, Amount, Date) VALUES (?, ?, ?);", 
                           (data['User_id'], data['Amount'], data['Date']))
            transaction_id = cursor.execute("SELECT @@IDENTITY;").fetchval()

            # 根据交易类型处理 Expenditure 或 Income 表
            if data['TransactionType'].lower() == '買入':
                cursor.execute("INSERT INTO Expenditure (User_id, Amount, ExpenditureDate, ExpenditureType_id) VALUES (?, ?, ?, ?);", 
                               (data['User_id'], data['Amount'], data['Date'], 4))
                expenditure_id = cursor.execute("SELECT @@IDENTITY;").fetchval()
                cursor.execute("UPDATE Transactions SET Expenditure_id = ? WHERE Transaction_id = ?;", 
                               (expenditure_id, transaction_id))
            else:
                cursor.execute("INSERT INTO Income (User_id, Amount, IncomeDate, IncomeType_id) VALUES (?, ?, ?, ?);",
                               (data['User_id'], data['Amount'], data['Date'], 4))
                income_id = cursor.execute("SELECT @@IDENTITY;").fetchval()
                cursor.execute("UPDATE Transactions SET Income_id = ? WHERE Transaction_id = ?;", 
                               (income_id, transaction_id))

            # 检查 Stock_id 是否存在于 Stock 表中
            stock_id_to_check = data['Stock_id']
            cursor.execute("SELECT * FROM Stock WHERE Stock_id = ?", stock_id_to_check)
            result = cursor.fetchone()

            if result is None:
                # Stock_id 不存在于 Stock 表中，插入新的 Stock 记录
                cursor.execute("INSERT INTO Stock (StockName, CurrentPrice, Date) VALUES (?, ?, ?);", 
                        (data['StockName'], data['Price'], data['Date']))

                # 获取新插入记录的标识值
                new_stock_id = cursor.execute("SELECT @@IDENTITY;").fetchval()
            else:
                # Stock_id 存在，使用现有记录的标识值
                new_stock_id = stock_id_to_check

            # 插入 Stock_Transaction 表
            cursor.execute("INSERT INTO Stock_Transaction (Transaction_id, Stock_id, SellOrBuy, Price, StockAmount) VALUES (?, ?, ?, ?, ?);", 
                        (transaction_id, new_stock_id, data['SellOrBuy'], data['Price'], data['StockAmount']))


            conn.commit()
    except Exception as e:
        return jsonify({'error': 'Database error', 'message': str(e)}), 500

    return jsonify({'message': 'Stock transaction added successfully'}), 201

@stock_blueprint.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Stock_Transaction WHERE Transaction_id = ?;", (transaction_id,))
        cursor.execute("DELETE FROM Transactions WHERE Transaction_id = ?;", (transaction_id,))
        conn.commit()
    return jsonify({'message': 'Transaction deleted successfully'}), 200


def update_stock_prices():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Stock_id, StockName FROM Stock;")
        stocks = cursor.fetchall()
        for stock_id, stock_name in stocks:
            current_price = get_current_stock_price(stock_name)
            if current_price is not None:
                cursor.execute("UPDATE Stock SET CurrentPrice = ?, Date = CURRENT_DATE WHERE Stock_id = ?;", 
                               (current_price, stock_id))
        conn.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(func=update_stock_prices, trigger="interval", hours=1)  # 每小时更新一次
scheduler.start()


@stock_blueprint.route('/user/<int:user_id>/stocks', methods=['GET'])
def get_user_stocks(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT st.Stock_id, s.StockName, st.Price, st.StockAmount, st.SellOrBuy
        FROM Stock_Transaction st
        JOIN Stock s ON st.Stock_id = s.Stock_id
        JOIN Transactions t ON st.Transaction_id = t.Transaction_id
        WHERE t.User_id = ?
        """, (user_id,))
        stocks = cursor.fetchall()
    stocks_info = [{'stock_id': stock[0], 'stock_name': stock[1], 'price': stock[2], 'quantity': stock[3], 'transaction_type': stock[4]} for stock in stocks]
    return jsonify(stocks_info), 200

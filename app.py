# app.py

import pyodbc
from flask import Flask
from flask_cors import CORS

from api.account import account_blueprint
from api.budget import budget_blueprint
from api.expenditure import expenditure_blueprint
from api.income import income_blueprint
from api.stock import stock_blueprint
from api.type import type_blueprint

app = Flask(__name__)
CORS(app)

# 定义全局变量来存储数据库连接字符串
app.config['DB_CONNECTION_STRING'] = (
    'Driver={ODBC Driver 18 for SQL Server};'
    'Server=tcp:db-accounting.database.windows.net,1433;'
    'Database=FMS_DB;'
    'Uid=catt;'
    'Pwd=Iamstupid4ever;'  # 请确保替换为您的密码
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)

# 创建数据库连接函数
def get_db_connection():
    conn = pyodbc.connect(app.config['DB_CONNECTION_STRING'], autocommit=True)
    return conn

app.register_blueprint(account_blueprint, url_prefix='/api')
app.register_blueprint(income_blueprint, url_prefix='/api')
app.register_blueprint(expenditure_blueprint, url_prefix='/api')
app.register_blueprint(budget_blueprint, url_prefix='/api')
app.register_blueprint(stock_blueprint, url_prefix='/api')
app.register_blueprint(type_blueprint, url_prefix='/api')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

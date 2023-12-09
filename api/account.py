# api/account.py

import hashlib

import pyodbc
from flask import Blueprint, current_app, jsonify, request

account_blueprint = Blueprint('account', __name__)

def get_db_connection():
    return pyodbc.connect(current_app.config['DB_CONNECTION_STRING'], autocommit=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@account_blueprint.route('/accounts/login', methods=['POST'])
def login():
    data = request.json
    account = data['account']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT User_id, Password FROM User_info WHERE Account = ?', account)
    account = cursor.fetchone()
    cursor.close()
    conn.close()

    if account and account[1] == password:
        return jsonify({'user_id': account[0]}), 200
    else:
        return jsonify({'message': 'Invalid account or password'}), 401

@account_blueprint.route('/accounts/register', methods=['POST'])
def register():
    data = request.json
    account = data['account']
    password = data['password']
    name = data['name']
    mail = data['mail']
    phone = data['phone']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO User_info (Account, Password, User_name, User_mail, User_phone) VALUES (?, ?, ?, ?, ?)', account, password, name, mail, phone)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Account created successfully.'}), 201

@account_blueprint.route('/accounts/<int:user_id>', methods=['GET'])
def get_account(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT User_id, User_name FROM User_info WHERE User_id = ?', user_id)
    account = cursor.fetchone()
    cursor.close()
    conn.close()

    if account:
        return jsonify({'user_id': account[0], 'username': account[1]})
    else:
        return jsonify({'message': 'Account not found'}), 404

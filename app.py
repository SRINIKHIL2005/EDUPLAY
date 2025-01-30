from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import google.generativeai as genai
import re

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-default-secret-key')  # Change this to a secure secret key

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['eduplay']
users = db['users']

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.route("/", methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/auth', methods=['POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = users.find_one({'username': username})
    
    if user and check_password_hash(user['password'], password):
        # Login successful
        return redirect(url_for('dashboard'))
    else:
        # Login failed
        flash('Invalid username or password')
        return redirect(url_for('login'))

@app.route("/like", methods=['GET', 'POST'])  
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate input
        if not all([username, email, password, confirm_password]):
            flash('All fields are required')
            return redirect(url_for('signup'))

        if not is_valid_email(email):
            flash('Please enter a valid email address')
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('signup'))

        # Check if username or email already exists
        if users.find_one({'$or': [{'username': username}, {'email': email}]}):
            flash('Username or email already exists')
            return redirect(url_for('signup'))

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = {
            'username': username,
            'email': email,
            'password': hashed_password
        }
        
        users.insert_one(new_user)
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('like.html')  # Updated the template name

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    return render_template('chatbot.html')

@app.route('/api/gemini', methods=['POST'])  # Properly linked the route
def gemini_api():
    genai.configure(api_key=os.getenv('AIzaSyAztzunEBlRUIcYQMYHIBapT6LNpMm4gx0'))
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    try:
        data = request.json
        message = data.get('message')
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        # Generate response using Gemini AI
        response = model.generate_content(message)
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

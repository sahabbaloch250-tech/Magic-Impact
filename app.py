from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
app.permanent_session_lifetime = timedelta(days=7)

# Database setup
def init_db():
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = c.fetchone()
    
    if table_exists:
        # Check if username column exists
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'username' not in columns:
            # Drop old table and create new one
            print("⚠️  Old table structure found. Recreating table...")
            c.execute("DROP TABLE users")
            conn.commit()
    
    # Create table with correct structure
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))
        
        hashed_password = hash_password(password)
        
        try:
            conn = sqlite3.connect('database/users.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                     (username, email, hashed_password))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        
        conn = sqlite3.connect('database/users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                 (username, hashed_password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session.permanent = True
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('home'))  # Redirect to home page
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/home')
def home():
    if 'username' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs('database', exist_ok=True)
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
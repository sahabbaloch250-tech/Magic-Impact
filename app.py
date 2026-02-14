from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
from datetime import timedelta, datetime
from werkzeug.utils import secure_filename

# PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.permanent_session_lifetime = timedelta(days=7)

# Upload folder for screenshots
UPLOAD_FOLDER = 'static/uploads/screenshots'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

# Check if running on Railway (PostgreSQL) or local (SQLite)
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Get database connection - PostgreSQL on Railway, SQLite locally"""
    if DATABASE_URL and POSTGRES_AVAILABLE:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn, 'postgres'
    else:
        # Add timeout to prevent lock issues
        conn = sqlite3.connect('database/users.db', timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn, 'sqlite'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    """Initialize database with proper schema"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        # PostgreSQL schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(200) NOT NULL,
                balance DECIMAL(10,2) DEFAULT 100.00,
                referral_code VARCHAR(20) UNIQUE,
                referred_by VARCHAR(20),
                whatsapp_number VARCHAR(20),
                easypaisa_number VARCHAR(20),
                jazzcash_number VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS investments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                plan_name VARCHAR(50) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                daily_income DECIMAL(10,2) NOT NULL,
                total_return DECIMAL(10,2) NOT NULL,
                days_remaining INTEGER DEFAULT 30,
                days_completed INTEGER DEFAULT 0,
                screenshot_url VARCHAR(500),
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                amount DECIMAL(10,2) NOT NULL,
                payment_method VARCHAR(20) NOT NULL,
                account_number VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_earnings (
                id SERIAL PRIMARY KEY,
                investment_id INTEGER REFERENCES investments(id),
                user_id INTEGER REFERENCES users(id),
                amount DECIMAL(10,2) NOT NULL,
                earned_date DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        print("✅ PostgreSQL Database initialized successfully!")
        
    else:
        # SQLite schema with migration
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'balance' not in columns:
                print("🔧 Adding 'balance' column...")
                cursor.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 100.00")
                cursor.execute("UPDATE users SET balance = 100.00 WHERE balance IS NULL")
            
            if 'whatsapp_number' not in columns:
                print("🔧 Adding 'whatsapp_number' column...")
                cursor.execute("ALTER TABLE users ADD COLUMN whatsapp_number TEXT")
            
            if 'easypaisa_number' not in columns:
                print("🔧 Adding 'easypaisa_number' column...")
                cursor.execute("ALTER TABLE users ADD COLUMN easypaisa_number TEXT")
            
            if 'jazzcash_number' not in columns:
                print("🔧 Adding 'jazzcash_number' column...")
                cursor.execute("ALTER TABLE users ADD COLUMN jazzcash_number TEXT")
            
            if 'referral_code' not in columns:
                print("🔧 Adding 'referral_code' column...")
                cursor.execute("ALTER TABLE users ADD COLUMN referral_code TEXT")
                # Note: UNIQUE constraint will be enforced in code, not DB for SQLite migration
            
            if 'referred_by' not in columns:
                print("🔧 Adding 'referred_by' column...")
                cursor.execute("ALTER TABLE users ADD COLUMN referred_by TEXT")
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    balance REAL DEFAULT 100.00,
                    referral_code TEXT UNIQUE,
                    referred_by TEXT,
                    whatsapp_number TEXT,
                    easypaisa_number TEXT,
                    jazzcash_number TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Check and recreate investments table if needed
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='investments'")
        inv_exists = cursor.fetchone()
        
        if inv_exists:
            cursor.execute("PRAGMA table_info(investments)")
            inv_columns = [column[1] for column in cursor.fetchall()]
            
            if 'plan_name' not in inv_columns or 'days_completed' not in inv_columns:
                print("🔧 Recreating investments table...")
                cursor.execute("DROP TABLE IF EXISTS investments")
                inv_exists = None
        
        if not inv_exists:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS investments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    plan_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    daily_income REAL NOT NULL,
                    total_return REAL NOT NULL,
                    days_remaining INTEGER DEFAULT 30,
                    days_completed INTEGER DEFAULT 0,
                    screenshot_url TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                account_number TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                investment_id INTEGER,
                user_id INTEGER,
                amount REAL NOT NULL,
                earned_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (investment_id) REFERENCES investments(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        print("✅ SQLite Database initialized successfully!")
    
    conn.commit()
    conn.close()

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
        
        # Get referral code from URL if present
        referral_code = request.args.get('ref', '').strip()
        
        try:
            conn, db_type = get_db_connection()
            cursor = conn.cursor()
            
            if db_type == 'postgres':
                cursor.execute(
                    "INSERT INTO users (username, email, password, referred_by) VALUES (%s, %s, %s, %s)",
                    (username, email, hashed_password, referral_code if referral_code else None)
                )
            else:
                cursor.execute(
                    "INSERT INTO users (username, email, password, referred_by) VALUES (?, ?, ?, ?)",
                    (username, email, hashed_password, referral_code if referral_code else None)
                )
            
            conn.commit()
            conn.close()
            
            print(f"✅ User registered: {username}, {email}" + (f" (Referred by: {referral_code})" if referral_code else ""))
            flash('Registration successful! Please login. You received 100 Rs signup bonus!', 'success')
            return redirect(url_for('login'))
            
        except (sqlite3.IntegrityError, Exception) as e:
            print(f"❌ Registration error: {str(e)}")
            flash('Username or email already exists!', 'error')
            return redirect(url_for('register'))
    
    # For GET request, get referral code from URL
    referral_code = request.args.get('ref', '')
    return render_template('register.html', referral_code=referral_code)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'postgres':
            cursor.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (username, hashed_password)
            )
        else:
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, hashed_password)
            )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session.permanent = True
            session['user_id'] = user['id'] if isinstance(user, dict) else user[0]
            session['username'] = user['username'] if isinstance(user, dict) else user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/invest', methods=['POST'])
def invest():
    if 'username' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    # Get form data with validation
    plan_name = request.form.get('plan_name', '').strip()
    amount_str = request.form.get('amount', '').strip()
    daily_income_str = request.form.get('daily_income', '').strip()
    whatsapp_number = request.form.get('whatsapp_number', '').strip()
    screenshot = request.files.get('screenshot')
    
    # Validate all fields
    if not plan_name or not amount_str or not daily_income_str:
        flash('All fields are required!', 'error')
        return redirect(url_for('home'))
    
    if not whatsapp_number:
        flash('WhatsApp number is required!', 'error')
        return redirect(url_for('home'))
    
    # Validate WhatsApp number (11 digits for Pakistan)
    if len(whatsapp_number) < 11 or not whatsapp_number.isdigit():
        flash('Please enter a valid 11-digit WhatsApp number!', 'error')
        return redirect(url_for('home'))
    
    try:
        amount = float(amount_str)
        daily_income = float(daily_income_str)
    except ValueError:
        flash('Invalid amount entered!', 'error')
        return redirect(url_for('home'))
    
    # Validate minimum amount
    if amount < 500:
        flash('Minimum investment amount is Rs 500!', 'error')
        return redirect(url_for('home'))
    
    # Validate screenshot
    if not screenshot or screenshot.filename == '':
        flash('Please upload payment screenshot!', 'error')
        return redirect(url_for('home'))
    
    # Check file type
    if not allowed_file(screenshot.filename):
        flash('Only image files (PNG, JPG, JPEG, GIF) are allowed!', 'error')
        return redirect(url_for('home'))
    
    # Calculate total return
    total_return = daily_income * 30
    
    # Save screenshot
    screenshot_url = None
    try:
        filename = secure_filename(f"{session['user_id']}_{int(datetime.now().timestamp())}_{screenshot.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        screenshot.save(filepath)
        screenshot_url = f'/static/uploads/screenshots/{filename}'
        print(f"✅ Screenshot saved: {filename}")
    except Exception as e:
        print(f"❌ Error saving screenshot: {str(e)}")
        flash('Error uploading screenshot. Please try again.', 'error')
        return redirect(url_for('home'))
    
    # Save investment to database
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update user's WhatsApp number
        if db_type == 'postgres':
            cursor.execute('UPDATE users SET whatsapp_number = %s WHERE id = %s', 
                         (whatsapp_number, session['user_id']))
        else:
            cursor.execute('UPDATE users SET whatsapp_number = ? WHERE id = ?', 
                         (whatsapp_number, session['user_id']))
        
        # Insert investment
        if db_type == 'postgres':
            cursor.execute('''
                INSERT INTO investments 
                (user_id, plan_name, amount, daily_income, total_return, screenshot_url, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (session['user_id'], plan_name, amount, daily_income, total_return, screenshot_url, 'pending'))
        else:
            cursor.execute('''
                INSERT INTO investments 
                (user_id, plan_name, amount, daily_income, total_return, screenshot_url, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], plan_name, amount, daily_income, total_return, screenshot_url, 'pending'))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Investment created: {plan_name} - Rs {amount} by {session['username']} (WhatsApp: {whatsapp_number})")
        flash('Investment submitted successfully! Admin will verify your payment screenshot.', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        conn.close()
        print(f"❌ Investment error: {str(e)}")
        flash(f'Investment failed: {str(e)}', 'error')
        return redirect(url_for('home'))

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'username' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        amount_str = request.form.get('amount', '').strip()
        payment_method = request.form.get('payment_method', '').strip()
        account_number = request.form.get('account_number', '').strip()
        
        # Validation
        if not amount_str or not payment_method or not account_number:
            flash('All fields are required!', 'error')
            return redirect(url_for('withdraw'))
        
        try:
            amount = float(amount_str)
        except ValueError:
            flash('Invalid amount entered!', 'error')
            return redirect(url_for('withdraw'))
        
        if amount < 250:
            flash('Minimum withdrawal amount is Rs 250!', 'error')
            return redirect(url_for('withdraw'))
        
        if payment_method not in ['easypaisa', 'jazzcash']:
            flash('Invalid payment method selected!', 'error')
            return redirect(url_for('withdraw'))
        
        # Validate account number format (basic)
        if len(account_number) < 11:
            flash('Invalid account number! Please enter valid mobile number.', 'error')
            return redirect(url_for('withdraw'))
        
        # Check balance
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'postgres':
            cursor.execute('SELECT balance FROM users WHERE id = %s', (session['user_id'],))
        else:
            cursor.execute('SELECT balance FROM users WHERE id = ?', (session['user_id'],))
        
        user = cursor.fetchone()
        current_balance = user['balance'] if isinstance(user, dict) else user[0]
        
        if amount > current_balance:
            flash(f'Insufficient balance! Your current balance is Rs {current_balance}', 'error')
            conn.close()
            return redirect(url_for('withdraw'))
        
        # Create withdrawal request
        try:
            if db_type == 'postgres':
                cursor.execute('''
                    INSERT INTO withdrawals (user_id, amount, payment_method, account_number, status)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (session['user_id'], amount, payment_method, account_number, 'pending'))
                
                cursor.execute('''
                    UPDATE users SET balance = balance - %s WHERE id = %s
                ''', (amount, session['user_id']))
                
                if payment_method == 'easypaisa':
                    cursor.execute('UPDATE users SET easypaisa_number = %s WHERE id = %s', 
                                 (account_number, session['user_id']))
                else:
                    cursor.execute('UPDATE users SET jazzcash_number = %s WHERE id = %s', 
                                 (account_number, session['user_id']))
            else:
                cursor.execute('''
                    INSERT INTO withdrawals (user_id, amount, payment_method, account_number, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session['user_id'], amount, payment_method, account_number, 'pending'))
                
                cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', 
                             (amount, session['user_id']))
                
                if payment_method == 'easypaisa':
                    cursor.execute('UPDATE users SET easypaisa_number = ? WHERE id = ?', 
                                 (account_number, session['user_id']))
                else:
                    cursor.execute('UPDATE users SET jazzcash_number = ? WHERE id = ?', 
                                 (account_number, session['user_id']))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Withdrawal request: Rs {amount} via {payment_method} by {session['username']}")
            flash(f'Withdrawal request of Rs {amount} submitted successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            conn.close()
            print(f"❌ Withdrawal error: {str(e)}")
            flash(f'Withdrawal failed: {str(e)}', 'error')
            return redirect(url_for('withdraw'))
    
    # GET request - show form
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        cursor.execute('SELECT balance, easypaisa_number, jazzcash_number FROM users WHERE id = %s', 
                      (session['user_id'],))
    else:
        cursor.execute('SELECT balance, easypaisa_number, jazzcash_number FROM users WHERE id = ?', 
                      (session['user_id'],))
    
    user = cursor.fetchone()
    conn.close()
    
    balance = user['balance'] if isinstance(user, dict) else user[0]
    easypaisa = user['easypaisa_number'] if isinstance(user, dict) else user[1]
    jazzcash = user['jazzcash_number'] if isinstance(user, dict) else user[2]
    
    return render_template('withdraw.html', 
                         username=session['username'],
                         balance=balance, 
                         easypaisa=easypaisa, 
                         jazzcash=jazzcash)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    # Get user balance
    if db_type == 'postgres':
        cursor.execute('SELECT balance FROM users WHERE id = %s', (session['user_id'],))
    else:
        cursor.execute('SELECT balance FROM users WHERE id = ?', (session['user_id'],))
    
    user = cursor.fetchone()
    balance = float(user['balance'] if isinstance(user, dict) else user[0])
    
    # Get all investments for this user
    if db_type == 'postgres':
        cursor.execute('''
            SELECT * FROM investments 
            WHERE user_id = %s
            ORDER BY created_at DESC
        ''', (session['user_id'],))
    else:
        cursor.execute('''
            SELECT * FROM investments 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (session['user_id'],))
    
    investments_raw = cursor.fetchall()
    
    # Calculate stats - ONLY for active investments
    total_invested = 0
    total_daily_income = 0
    total_earned = 0
    
    for inv in investments_raw:
        status = inv['status'] if isinstance(inv, dict) else inv[9]
        if status == 'active':
            amount = float(inv['amount'] if isinstance(inv, dict) else inv[3])
            daily_income = float(inv['daily_income'] if isinstance(inv, dict) else inv[4])
            days_completed = int(inv['days_completed'] if isinstance(inv, dict) else inv[7])
            
            total_invested += amount
            total_daily_income += daily_income
            total_earned += (daily_income * days_completed)
    
    # Format investments for template
    investments = []
    for inv in investments_raw:
        if isinstance(inv, dict):
            inv_data = dict(inv)
        else:
            inv_data = {
                'id': inv[0],
                'user_id': inv[1],
                'plan_name': inv[2],
                'amount': float(inv[3]),
                'daily_income': float(inv[4]),
                'total_return': float(inv[5]),
                'days_remaining': int(inv[6]),
                'days_completed': int(inv[7]),
                'screenshot_url': inv[8],
                'status': inv[9],
                'created_at': str(inv[10]) if inv[10] else '',
                'approved_at': str(inv[11]) if len(inv) > 11 and inv[11] else None
            }
        
        investments.append(inv_data)
    
    conn.close()
    
    return render_template('dashboard.html', 
                         username=session['username'],
                         balance=round(balance, 2),
                         total_invested=round(total_invested, 2),
                         total_daily_income=round(total_daily_income, 2),
                         total_earned=round(total_earned, 2),
                         investments=investments)

@app.route('/home')
def home():
    if 'username' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/referral')
def referral():
    if 'username' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    # Get or create user's referral code
    if db_type == 'postgres':
        cursor.execute('SELECT referral_code FROM users WHERE id = %s', (session['user_id'],))
    else:
        cursor.execute('SELECT referral_code FROM users WHERE id = ?', (session['user_id'],))
    
    user = cursor.fetchone()
    referral_code = user['referral_code'] if isinstance(user, dict) else user[0]
    
    # Generate referral code if not exists
    if not referral_code:
        import random
        import string
        
        # Keep trying until we get a unique code
        max_attempts = 10
        for attempt in range(max_attempts):
            referral_code = session['username'].upper()[:4] + ''.join(random.choices(string.digits, k=4))
            
            # Check if code already exists
            if db_type == 'postgres':
                cursor.execute('SELECT id FROM users WHERE referral_code = %s', (referral_code,))
            else:
                cursor.execute('SELECT id FROM users WHERE referral_code = ?', (referral_code,))
            
            existing = cursor.fetchone()
            if not existing:
                break  # Code is unique
        
        # Update user with unique referral code
        if db_type == 'postgres':
            cursor.execute('UPDATE users SET referral_code = %s WHERE id = %s', 
                         (referral_code, session['user_id']))
        else:
            cursor.execute('UPDATE users SET referral_code = ? WHERE id = ?', 
                         (referral_code, session['user_id']))
        conn.commit()
    
    # Get referral stats
    if db_type == 'postgres':
        cursor.execute('''
            SELECT COUNT(*) as total FROM users WHERE referred_by = %s
        ''', (referral_code,))
    else:
        cursor.execute('''
            SELECT COUNT(*) as total FROM users WHERE referred_by = ?
        ''', (referral_code,))
    
    total_ref = cursor.fetchone()
    total_referrals = total_ref['total'] if isinstance(total_ref, dict) else total_ref[0]
    
    # Get referred users list
    if db_type == 'postgres':
        cursor.execute('''
            SELECT username, created_at FROM users 
            WHERE referred_by = %s
            ORDER BY created_at DESC
        ''', (referral_code,))
    else:
        cursor.execute('''
            SELECT username, created_at FROM users 
            WHERE referred_by = ?
            ORDER BY created_at DESC
        ''', (referral_code,))
    
    referrals_raw = cursor.fetchall()
    conn.close()
    
    # Format referrals
    referrals = []
    for ref in referrals_raw:
        referrals.append({
            'username': ref['username'] if isinstance(ref, dict) else ref[0],
            'joined_date': ref['created_at'] if isinstance(ref, dict) else ref[1],
            'total_investment': 0,  # TODO: Calculate from investments
            'commission_earned': 0   # TODO: Calculate commission
        })
    
    # Create referral link
    referral_link = f"http://localhost:5000/register?ref={referral_code}"
    
    return render_template('referral.html',
                         username=session['username'],
                         referral_code=referral_code,
                         referral_link=referral_link,
                         total_referrals=total_referrals,
                         active_referrals=total_referrals,
                         total_commission=0,
                         pending_commission=0,
                         referrals=referrals)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Admin Routes
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid admin credentials!', 'error')
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/admin')
def admin_panel():
    if 'admin' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    # Get pending investments with user info
    if db_type == 'postgres':
        cursor.execute('''
            SELECT i.*, u.username, u.whatsapp_number 
            FROM investments i
            JOIN users u ON i.user_id = u.id
            ORDER BY i.created_at DESC
        ''')
    else:
        cursor.execute('''
            SELECT i.*, u.username, u.whatsapp_number 
            FROM investments i
            JOIN users u ON i.user_id = u.id
            ORDER BY i.created_at DESC
        ''')
    investments = cursor.fetchall()
    
    # Get pending withdrawals with user info
    if db_type == 'postgres':
        cursor.execute('''
            SELECT w.*, u.username 
            FROM withdrawals w
            JOIN users u ON w.user_id = u.id
            ORDER BY w.created_at DESC
        ''')
    else:
        cursor.execute('''
            SELECT w.*, u.username 
            FROM withdrawals w
            JOIN users u ON w.user_id = u.id
            ORDER BY w.created_at DESC
        ''')
    withdrawals = cursor.fetchall()
    
    # Get all users
    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM investments WHERE status='pending'")
    pending_inv = cursor.fetchone()
    pending_investments_count = pending_inv[0] if pending_inv else 0
    
    cursor.execute("SELECT COUNT(*) FROM withdrawals WHERE status='pending'")
    pending_wd = cursor.fetchone()
    pending_withdrawals_count = pending_wd[0] if pending_wd else 0
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users_count = cursor.fetchone()
    total_users = total_users_count[0] if total_users_count else 0
    
    cursor.execute("SELECT SUM(amount) FROM investments WHERE status='active'")
    total_inv = cursor.fetchone()
    total_invested = total_inv[0] if total_inv and total_inv[0] else 0
    
    conn.close()
    
    # Format data for template
    investments_list = []
    for inv in investments:
        if isinstance(inv, dict):
            investments_list.append(dict(inv))
        else:
            investments_list.append({
                'id': inv[0],
                'user_id': inv[1],
                'plan_name': inv[2],
                'amount': inv[3],
                'daily_income': inv[4],
                'total_return': inv[5],
                'days_remaining': inv[6],
                'days_completed': inv[7],
                'screenshot_url': inv[8],
                'status': inv[9],
                'created_at': inv[10],
                'username': inv[12],
                'whatsapp_number': inv[13] if len(inv) > 13 else None
            })
    
    withdrawals_list = []
    for wd in withdrawals:
        if isinstance(wd, dict):
            withdrawals_list.append(dict(wd))
        else:
            withdrawals_list.append({
                'id': wd[0],
                'user_id': wd[1],
                'amount': wd[2],
                'payment_method': wd[3],
                'account_number': wd[4],
                'status': wd[5],
                'created_at': wd[6],
                'username': wd[8]
            })
    
    users_list = []
    for user in users:
        if isinstance(user, dict):
            users_list.append(dict(user))
        else:
            users_list.append({
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'balance': user[4],
                'whatsapp_number': user[5] if len(user) > 5 else None,
                'created_at': user[8] if len(user) > 8 else user[7]
            })
    
    return render_template('admin.html',
                         investments=investments_list,
                         withdrawals=withdrawals_list,
                         users=users_list,
                         pending_investments_count=pending_investments_count,
                         pending_withdrawals_count=pending_withdrawals_count,
                         total_users=total_users,
                         total_invested=total_invested)

@app.route('/admin/approve-investment/<int:investment_id>', methods=['POST'])
def approve_investment(investment_id):
    if 'admin' not in session:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('admin_login'))
    
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update investment status to active
        if db_type == 'postgres':
            cursor.execute('''
                UPDATE investments 
                SET status = %s, approved_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            ''', ('active', investment_id))
        else:
            cursor.execute('''
                UPDATE investments 
                SET status = ?, approved_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', ('active', investment_id))
        
        conn.commit()
        conn.close()
        
        flash('Investment approved successfully!', 'success')
        print(f"✅ Investment #{investment_id} approved by admin")
        
    except Exception as e:
        conn.close()
        flash(f'Error approving investment: {str(e)}', 'error')
        print(f"❌ Error approving investment: {str(e)}")
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/reject-investment/<int:investment_id>', methods=['POST'])
def reject_investment(investment_id):
    if 'admin' not in session:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('admin_login'))
    
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update investment status to rejected
        if db_type == 'postgres':
            cursor.execute('''
                UPDATE investments 
                SET status = %s 
                WHERE id = %s
            ''', ('rejected', investment_id))
        else:
            cursor.execute('''
                UPDATE investments 
                SET status = ? 
                WHERE id = ?
            ''', ('rejected', investment_id))
        
        conn.commit()
        conn.close()
        
        flash('Investment rejected!', 'success')
        print(f"❌ Investment #{investment_id} rejected by admin")
        
    except Exception as e:
        conn.close()
        flash(f'Error rejecting investment: {str(e)}', 'error')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/approve-withdrawal/<int:withdrawal_id>', methods=['POST'])
def approve_withdrawal(withdrawal_id):
    if 'admin' not in session:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('admin_login'))
    
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update withdrawal status to approved
        if db_type == 'postgres':
            cursor.execute('''
                UPDATE withdrawals 
                SET status = %s, processed_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            ''', ('approved', withdrawal_id))
        else:
            cursor.execute('''
                UPDATE withdrawals 
                SET status = ?, processed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', ('approved', withdrawal_id))
        
        conn.commit()
        conn.close()
        
        flash('Withdrawal approved successfully!', 'success')
        print(f"✅ Withdrawal #{withdrawal_id} approved by admin")
        
    except Exception as e:
        conn.close()
        flash(f'Error approving withdrawal: {str(e)}', 'error')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/reject-withdrawal/<int:withdrawal_id>', methods=['POST'])
def reject_withdrawal(withdrawal_id):
    if 'admin' not in session:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('admin_login'))
    
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get withdrawal details to refund balance
        if db_type == 'postgres':
            cursor.execute('SELECT user_id, amount FROM withdrawals WHERE id = %s', (withdrawal_id,))
        else:
            cursor.execute('SELECT user_id, amount FROM withdrawals WHERE id = ?', (withdrawal_id,))
        
        withdrawal = cursor.fetchone()
        
        if withdrawal:
            user_id = withdrawal['user_id'] if isinstance(withdrawal, dict) else withdrawal[0]
            amount = withdrawal['amount'] if isinstance(withdrawal, dict) else withdrawal[1]
            
            # Refund balance
            if db_type == 'postgres':
                cursor.execute('UPDATE users SET balance = balance + %s WHERE id = %s', (amount, user_id))
                cursor.execute('UPDATE withdrawals SET status = %s WHERE id = %s', ('rejected', withdrawal_id))
            else:
                cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
                cursor.execute('UPDATE withdrawals SET status = ? WHERE id = ?', ('rejected', withdrawal_id))
            
            conn.commit()
            flash(f'Withdrawal rejected! Rs {amount} refunded to user balance.', 'success')
            print(f"❌ Withdrawal #{withdrawal_id} rejected, Rs {amount} refunded")
        
        conn.close()
        
    except Exception as e:
        conn.close()
        flash(f'Error rejecting withdrawal: {str(e)}', 'error')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

# Debug route (remove in production)
@app.route('/debug-db')
def debug_db():
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM users')
        count = cursor.fetchone()
        
        cursor.execute('SELECT id, username, email, balance, whatsapp_number, created_at FROM users ORDER BY created_at DESC LIMIT 10')
        users = cursor.fetchall()
        
        cursor.execute('SELECT COUNT(*) as count FROM investments')
        inv_count = cursor.fetchone()
        
        cursor.execute('''
            SELECT i.id, i.user_id, u.username, i.plan_name, i.amount, i.daily_income, 
                   i.status, i.days_completed, i.created_at, i.approved_at
            FROM investments i
            JOIN users u ON i.user_id = u.id
            ORDER BY i.created_at DESC
            LIMIT 20
        ''')
        investments = cursor.fetchall()
        
        conn.close()
        
        result = f"<h2>Database Debug Info</h2>"
        result += f"<p>Database Type: <strong>{db_type.upper()}</strong></p>"
        result += f"<p>Total Users: <strong>{count['count'] if isinstance(count, dict) else count[0]}</strong></p>"
        result += f"<p>Total Investments: <strong>{inv_count['count'] if isinstance(inv_count, dict) else inv_count[0]}</strong></p>"
        
        result += "<h3>Recent Users:</h3><ul>"
        for user in users:
            username = user['username'] if isinstance(user, dict) else user[1]
            email = user['email'] if isinstance(user, dict) else user[2]
            balance = user['balance'] if isinstance(user, dict) else user[3]
            whatsapp = user['whatsapp_number'] if isinstance(user, dict) else user[4]
            result += f"<li>{username} - {email} - Balance: Rs {balance} - WhatsApp: {whatsapp or 'Not set'}</li>"
        result += "</ul>"
        
        result += "<h3>Recent Investments:</h3><table border='1' cellpadding='10' style='border-collapse: collapse;'>"
        result += "<tr><th>ID</th><th>User</th><th>Plan</th><th>Amount</th><th>Daily Income</th><th>Status</th><th>Days Done</th><th>Created</th><th>Approved</th></tr>"
        for inv in investments:
            inv_id = inv['id'] if isinstance(inv, dict) else inv[0]
            username = inv['username'] if isinstance(inv, dict) else inv[2]
            plan = inv['plan_name'] if isinstance(inv, dict) else inv[3]
            amount = inv['amount'] if isinstance(inv, dict) else inv[4]
            daily = inv['daily_income'] if isinstance(inv, dict) else inv[5]
            status = inv['status'] if isinstance(inv, dict) else inv[6]
            days = inv['days_completed'] if isinstance(inv, dict) else inv[7]
            created = inv['created_at'] if isinstance(inv, dict) else inv[8]
            approved = inv['approved_at'] if isinstance(inv, dict) else inv[9] if len(inv) > 9 else None
            
            status_color = 'green' if status == 'active' else ('orange' if status == 'pending' else 'red')
            result += f"<tr>"
            result += f"<td>#{inv_id}</td>"
            result += f"<td>{username}</td>"
            result += f"<td><b>{plan}</b></td>"
            result += f"<td>Rs {amount}</td>"
            result += f"<td>Rs {daily}</td>"
            result += f"<td style='color:{status_color};font-weight:bold;'>{status.upper()}</td>"
            result += f"<td>{days}/30</td>"
            result += f"<td>{str(created)[:16] if created else 'N/A'}</td>"
            result += f"<td>{str(approved)[:16] if approved else 'Not yet'}</td>"
            result += f"</tr>"
        result += "</table>"
        
        return result
        
    except Exception as e:
        return f"<h2>Error:</h2><p>{str(e)}</p>"

if __name__ == '__main__':
    # Only create local folders if not using Railway/PostgreSQL
    if not os.environ.get('DATABASE_URL'):
        os.makedirs('database', exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    init_db()
    
    # Use Railway's PORT or default to 5000 for local
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
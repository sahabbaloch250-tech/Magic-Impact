"""
Balance Manager - Add, Remove, Check Balance
Complete testing tool
"""

import sqlite3
from datetime import datetime

def show_menu():
    print("\n" + "=" * 60)
    print("💰 BALANCE MANAGER")
    print("=" * 60)
    print("\n1. View All Users & Balances")
    print("2. Add Balance to User")
    print("3. Remove Balance from User")
    print("4. Set Exact Balance")
    print("5. Test Withdrawal (Deduct)")
    print("6. View User Details")
    print("0. Exit")
    print("=" * 60)

def view_all_users():
    conn = sqlite3.connect('database/users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, balance, whatsapp_number, created_at 
        FROM users 
        ORDER BY created_at DESC
    """)
    users = cursor.fetchall()
    
    print("\n📊 ALL USERS:")
    print("-" * 70)
    print(f"{'Username':<15} {'Balance':<12} {'WhatsApp':<15} {'Joined'}")
    print("-" * 70)
    
    for user in users:
        username = user[0]
        balance = user[1]
        whatsapp = user[2] or 'N/A'
        joined = user[3][:10] if user[3] else 'N/A'
        print(f"{username:<15} Rs {balance:<9.2f} {whatsapp:<15} {joined}")
    
    conn.close()

def add_balance():
    username = input("\nEnter username: ").strip()
    amount = float(input("Enter amount to ADD (Rs): "))
    
    conn = sqlite3.connect('database/users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User '{username}' not found!")
        conn.close()
        return
    
    old_balance = user[0]
    new_balance = old_balance + amount
    
    cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", 
                  (amount, username))
    conn.commit()
    conn.close()
    
    print(f"\n✅ SUCCESS!")
    print(f"User: {username}")
    print(f"Old Balance: Rs {old_balance:.2f}")
    print(f"Added: Rs {amount:.2f}")
    print(f"New Balance: Rs {new_balance:.2f}")

def remove_balance():
    username = input("\nEnter username: ").strip()
    amount = float(input("Enter amount to REMOVE (Rs): "))
    
    conn = sqlite3.connect('database/users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User '{username}' not found!")
        conn.close()
        return
    
    old_balance = user[0]
    
    if old_balance < amount:
        print(f"⚠️  Warning: Balance will go negative!")
        print(f"Current: Rs {old_balance:.2f}, Removing: Rs {amount:.2f}")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            conn.close()
            return
    
    new_balance = old_balance - amount
    
    cursor.execute("UPDATE users SET balance = balance - ? WHERE username = ?", 
                  (amount, username))
    conn.commit()
    conn.close()
    
    print(f"\n✅ SUCCESS!")
    print(f"User: {username}")
    print(f"Old Balance: Rs {old_balance:.2f}")
    print(f"Removed: Rs {amount:.2f}")
    print(f"New Balance: Rs {new_balance:.2f}")

def set_exact_balance():
    username = input("\nEnter username: ").strip()
    new_balance = float(input("Enter exact balance to SET (Rs): "))
    
    conn = sqlite3.connect('database/users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User '{username}' not found!")
        conn.close()
        return
    
    old_balance = user[0]
    
    cursor.execute("UPDATE users SET balance = ? WHERE username = ?", 
                  (new_balance, username))
    conn.commit()
    conn.close()
    
    print(f"\n✅ SUCCESS!")
    print(f"User: {username}")
    print(f"Old Balance: Rs {old_balance:.2f}")
    print(f"New Balance: Rs {new_balance:.2f}")

def test_withdrawal():
    username = input("\nEnter username: ").strip()
    amount = float(input("Withdrawal amount (Rs): "))
    
    if amount < 250:
        print("⚠️  Minimum withdrawal is Rs 250!")
        return
    
    conn = sqlite3.connect('database/users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User '{username}' not found!")
        conn.close()
        return
    
    balance = user[0]
    
    if balance < amount:
        print(f"❌ Insufficient balance!")
        print(f"Current Balance: Rs {balance:.2f}")
        print(f"Requested: Rs {amount:.2f}")
        conn.close()
        return
    
    new_balance = balance - amount
    
    cursor.execute("UPDATE users SET balance = balance - ? WHERE username = ?", 
                  (amount, username))
    conn.commit()
    conn.close()
    
    print(f"\n✅ WITHDRAWAL PROCESSED!")
    print(f"User: {username}")
    print(f"Withdrawn: Rs {amount:.2f}")
    print(f"Remaining Balance: Rs {new_balance:.2f}")

def view_user_details():
    username = input("\nEnter username: ").strip()
    
    conn = sqlite3.connect('database/users.db')
    cursor = conn.cursor()
    
    # User info
    cursor.execute("""
        SELECT id, username, email, balance, whatsapp_number, 
               easypaisa_number, jazzcash_number, created_at
        FROM users WHERE username = ?
    """, (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User '{username}' not found!")
        conn.close()
        return
    
    print(f"\n👤 USER DETAILS:")
    print("-" * 60)
    print(f"ID: {user[0]}")
    print(f"Username: {user[1]}")
    print(f"Email: {user[2]}")
    print(f"Balance: Rs {user[3]:.2f}")
    print(f"WhatsApp: {user[4] or 'Not set'}")
    print(f"EasyPaisa: {user[5] or 'Not set'}")
    print(f"JazzCash: {user[6] or 'Not set'}")
    print(f"Joined: {user[7][:10] if user[7] else 'N/A'}")
    
    # Investments
    cursor.execute("""
        SELECT plan_name, amount, daily_income, status, created_at
        FROM investments WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user[0],))
    investments = cursor.fetchall()
    
    if investments:
        print(f"\n💰 INVESTMENTS:")
        print("-" * 60)
        for inv in investments:
            print(f"{inv[0]}: Rs {inv[1]} (Daily: Rs {inv[2]}) - {inv[3].upper()}")
    
    # Withdrawals
    cursor.execute("""
        SELECT amount, payment_method, status, created_at
        FROM withdrawals WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 5
    """, (user[0],))
    withdrawals = cursor.fetchall()
    
    if withdrawals:
        print(f"\n💳 RECENT WITHDRAWALS:")
        print("-" * 60)
        for wd in withdrawals:
            print(f"Rs {wd[0]} via {wd[1].upper()} - {wd[2].upper()}")
    
    conn.close()

def main():
    while True:
        show_menu()
        choice = input("\nSelect option: ").strip()
        
        try:
            if choice == '1':
                view_all_users()
            elif choice == '2':
                add_balance()
            elif choice == '3':
                remove_balance()
            elif choice == '4':
                set_exact_balance()
            elif choice == '5':
                test_withdrawal()
            elif choice == '6':
                view_user_details()
            elif choice == '0':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid option!")
        except ValueError:
            print("❌ Invalid input! Please enter a number.")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
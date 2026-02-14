"""
Add Balance to User
Quick script to add money for testing
"""

import sqlite3

def add_balance():
    print("=" * 60)
    print("ADD BALANCE TO USER")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('database/users.db')
        cursor = conn.cursor()
        
        # Show all users
        print("\n📊 Current Users:")
        cursor.execute("SELECT username, balance FROM users")
        users = cursor.fetchall()
        
        print("\nUsername          | Current Balance")
        print("-" * 40)
        for user in users:
            print(f"{user[0]:15} | Rs {user[1]}")
        
        # Get input
        print("\n" + "=" * 60)
        username = input("Enter username: ").strip()
        amount = float(input("Enter amount to add (Rs): "))
        
        # Check if user exists
        cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"\n❌ User '{username}' not found!")
            conn.close()
            return
        
        current_balance = user[0]
        new_balance = current_balance + amount
        
        # Update balance
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", 
                      (amount, username))
        conn.commit()
        
        print("\n✅ SUCCESS!")
        print(f"User: {username}")
        print(f"Previous Balance: Rs {current_balance}")
        print(f"Added: Rs {amount}")
        print(f"New Balance: Rs {new_balance}")
        
        conn.close()
        
    except ValueError:
        print("\n❌ Invalid amount! Please enter a number.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    add_balance()
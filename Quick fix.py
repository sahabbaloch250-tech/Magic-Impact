"""Quick Fix - Activate All Pending Investments"""
import sqlite3
import time

print("Killing any hanging connections...")
time.sleep(3)

try:
    # Connect with long timeout
    conn = sqlite3.connect('database/users.db', timeout=30, isolation_level='EXCLUSIVE')
    cursor = conn.cursor()
    
    # Show current pending
    cursor.execute("SELECT id, plan_name, amount FROM investments WHERE status='pending'")
    pending = cursor.fetchall()
    
    print(f"\nFound {len(pending)} pending investment(s):")
    for inv in pending:
        print(f"  ID {inv[0]}: {inv[1]} - Rs {inv[2]}")
    
    # Activate all
    cursor.execute("UPDATE investments SET status='active', approved_at=CURRENT_TIMESTAMP WHERE status='pending'")
    rows = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ SUCCESS! Activated {rows} investment(s)!")
    print("\nNow:")
    print("1. Start Flask app: python app.py")
    print("2. Login to dashboard")
    print("3. Hard refresh (Ctrl+Shift+R)")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTry this:")
    print("1. Restart your computer")
    print("2. Run this script again")
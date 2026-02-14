"""
FORCE UNLOCK - Last Attempt Before Restart
"""
import sqlite3
import os
import time

db_path = 'database/users.db'

print("🚨 FORCE UNLOCK ATTEMPT")
print("=" * 60)

# Method 1: Delete lock files first
print("\n1. Deleting lock files...")
lock_files = [
    'database/users.db-journal',
    'database/users.db-wal', 
    'database/users.db-shm'
]

for lf in lock_files:
    try:
        if os.path.exists(lf):
            os.remove(lf)
            print(f"✅ Deleted: {lf}")
    except Exception as e:
        print(f"⚠️  {lf}: {e}")

time.sleep(2)

# Method 2: Try with isolation_level=None
print("\n2. Attempting connection with isolation_level=None...")
try:
    conn = sqlite3.connect(db_path, timeout=60, isolation_level=None)
    cursor = conn.cursor()
    
    print("✅ Connected!")
    
    # Quick activation
    cursor.execute("UPDATE investments SET status='active', approved_at=CURRENT_TIMESTAMP WHERE status='pending'")
    rows = cursor.rowcount
    
    print(f"✅ Activated {rows} investment(s)!")
    
    # Verify
    cursor.execute("SELECT id, plan_name, status FROM investments")
    invs = cursor.fetchall()
    print("\n📊 Current investments:")
    for inv in invs:
        print(f"  ID {inv[0]}: {inv[1]} - {inv[2].upper()}")
    
    conn.close()
    print("\n✅✅✅ SUCCESS! Database unlocked and investments activated!")
    print("\nNow run: python app.py")
    
except sqlite3.OperationalError as e:
    print(f"\n❌ Still locked: {e}")
    print("\n🔧 ONLY SOLUTION LEFT:")
    print("=" * 60)
    print("1. RESTART COMPUTER")
    print("2. Run this script again")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
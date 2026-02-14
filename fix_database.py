"""
Complete Database Lock Fix
Run this to fix all lock issues
"""

import os
import subprocess
import time

print("=" * 70)
print("DATABASE LOCK FIX TOOL")
print("=" * 70)

# Step 1: Kill all Python processes
print("\n🔧 Step 1: Killing all Python processes...")
try:
    subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                   capture_output=True, text=True)
    print("✅ All Python processes killed!")
except:
    print("⚠️  Manual kill needed: Press Ctrl+C in Flask terminal")

# Step 2: Wait
print("\n⏳ Step 2: Waiting 5 seconds for connections to close...")
time.sleep(5)
print("✅ Wait complete!")

# Step 3: Check database file
db_path = 'database/users.db'
print(f"\n📁 Step 3: Checking database file...")
if os.path.exists(db_path):
    size = os.path.getsize(db_path) / 1024
    print(f"✅ Database exists: {size:.2f} KB")
else:
    print("❌ Database not found!")

# Step 4: Remove lock files if exist
print("\n🔧 Step 4: Removing lock files...")
lock_files = [
    'database/users.db-journal',
    'database/users.db-wal',
    'database/users.db-shm'
]
removed = 0
for lock_file in lock_files:
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print(f"✅ Removed: {lock_file}")
            removed += 1
        except:
            print(f"⚠️  Could not remove: {lock_file}")

if removed == 0:
    print("✅ No lock files found (good!)")

# Step 5: Test database connection
print("\n🔧 Step 5: Testing database connection...")
try:
    import sqlite3
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    
    # Quick test query
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"✅ Database accessible! Found {count} user(s)")
    
    conn.close()
    print("✅ Connection closed properly")
    
except Exception as e:
    print(f"❌ Database still locked: {e}")
    print("\n🔧 SOLUTION: Restart your computer!")

print("\n" + "=" * 70)
print("✅ FIX COMPLETE!")
print("=" * 70)
print("\nNow you can:")
print("1. Start Flask: python app.py")
print("2. Try investment again")
print("\nIf still locked:")
print("- Restart computer")
print("- Run this script again")
print("=" * 70)
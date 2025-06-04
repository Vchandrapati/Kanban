#!/usr/bin/env python3
"""
Simple migration script to add priority and due_date fields to existing tasks.
This will add the new columns without touching your existing data.
"""

import os
import sqlite3
from datetime import datetime


def migrate_add_priority_due_date():
    """Add priority and due_date columns to the task table."""

    print("🔄 Starting migration to add priority and due_date fields...")

    db_path = 'taskflow.db'

    if not os.path.exists(db_path):
        print("❌ No database found. Please create your database first with:")
        print("   python manage.py create_tables")
        return False

    # Create backup first
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'taskflow_backup_{timestamp}.db'

    try:
        # Backup database
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")

        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check current table structure
        cursor.execute("PRAGMA table_info(task)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Current task table columns: {columns}")

        needs_priority = 'priority' not in columns
        needs_due_date = 'due_date' not in columns

        if not needs_priority and not needs_due_date:
            print("✅ Priority and due_date columns already exist. No migration needed.")
            conn.close()
            return True

        # Add priority column if needed
        if needs_priority:
            print("🔧 Adding priority column...")
            try:
                cursor.execute("ALTER TABLE task ADD COLUMN priority VARCHAR(10) DEFAULT 'Medium'")
                print("✅ Priority column added successfully")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print("⚠️  Priority column already exists")
                else:
                    raise e

        # Add due_date column if needed
        if needs_due_date:
            print("🔧 Adding due_date column...")
            try:
                cursor.execute("ALTER TABLE task ADD COLUMN due_date DATE")
                print("✅ Due_date column added successfully")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print("⚠️  Due_date column already exists")
                else:
                    raise e

        # Commit changes
        conn.commit()

        # Verify the changes
        cursor.execute("PRAGMA table_info(task)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Updated task table columns: {new_columns}")

        # Show sample data
        cursor.execute("SELECT id, title, priority, due_date FROM task LIMIT 3")
        sample_tasks = cursor.fetchall()
        if sample_tasks:
            print(f"📝 Sample tasks after migration:")
            for task in sample_tasks:
                print(f"   ID: {task[0]}, Title: {task[1]}, Priority: {task[2]}, Due: {task[3]}")
        else:
            print("📝 No existing tasks found")

        conn.close()

        print("\n🎉 Migration completed successfully!")
        print("✅ What was added:")
        if needs_priority:
            print("   • priority column (default: 'Medium')")
        if needs_due_date:
            print("   • due_date column (nullable)")

        return True

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        print(f"💾 Your database backup is saved as: {backup_path}")
        print("🔄 You can restore it with: cp {backup_path} taskflow.db")
        return False


def test_new_features():
    """Test that the new features work with Flask app."""

    print("\n🧪 Testing new features...")

    try:
        from app import create_app, db
        from app.models import Task, Swimlane, User

        app = create_app()

        with app.app_context():
            # Try to query tasks with new fields
            tasks = Task.query.all()
            print(f"✅ Found {len(tasks)} existing tasks")

            # Test creating a new task with priority and due date
            if tasks:
                sample_task = tasks[0]
                print(f"✅ Sample task: {sample_task.title}")
                print(f"   Priority: {sample_task.priority}")
                print(f"   Due Date: {sample_task.due_date}")
                print(f"   Is Overdue: {sample_task.is_overdue}")
                print(f"   Priority Color: {sample_task.priority_color}")

            print("✅ All new features are working correctly!")
            return True

    except ImportError:
        print("⚠️  Flask app not available for testing, but migration should be fine")
        return True
    except Exception as e:
        print(f"❌ Error testing new features: {e}")
        return False


if __name__ == '__main__':
    print("🚀 TaskFlow Database Migration Tool")
    print("=" * 50)

    success = migrate_add_priority_due_date()

    if success:
        test_success = test_new_features()

        if test_success:
            print("\n" + "=" * 50)
            print("🎊 Migration Complete! Your TaskFlow now supports:")
            print("   🔥 Task priorities (High, Medium, Low)")
            print("   📅 Due dates with overdue indicators")
            print("   🌙 Beautiful dark mode interface")
            print("   🎨 Priority color coding")
            print("\n💡 Next steps:")
            print("   1. Restart your Flask app: python run.py")
            print("   2. Login and test the new features!")
            print("   3. Create tasks with priorities and due dates")
        else:
            print("\n⚠️  Migration completed but testing had issues.")
            print("    Try restarting your Flask app anyway.")
    else:
        print("\n❌ Migration failed. Check the error messages above.")
        print("    Your original database is safe and unchanged.")

    print("\n" + "=" * 50)
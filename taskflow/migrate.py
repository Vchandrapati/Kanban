#!/usr/bin/env python3
"""
Database migration script to handle schema changes.
This will backup your existing data and recreate the database with the new schema.
"""

import os
import sqlite3
import shutil
from datetime import datetime
from app import create_app, db
from app.models import User, Swimlane, Task


def backup_existing_data():
    """Backup existing data from the old database."""
    db_path = 'taskflow.db'

    if not os.path.exists(db_path):
        print("No existing database found. Creating fresh database.")
        return None

    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'taskflow_backup_{timestamp}.db'
    shutil.copy2(db_path, backup_path)
    print(f"Database backed up to: {backup_path}")

    # Extract existing data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    existing_data = {
        'users': [],
        'tasks': []
    }

    try:
        # Try to get users (old schema might have 'password' instead of 'password_hash')
        try:
            cursor.execute("SELECT id, username, password FROM user")
            existing_data['users'] = cursor.fetchall()
            print(f"Found {len(existing_data['users'])} existing users")
        except sqlite3.OperationalError:
            try:
                cursor.execute("SELECT id, username FROM user")
                users = cursor.fetchall()
                # Convert to expected format with default password
                existing_data['users'] = [(id, username, 'defaultpass123') for id, username in users]
                print(f"Found {len(existing_data['users'])} existing users (no password field)")
            except sqlite3.OperationalError:
                print("No user table found in existing database")

        # Try to get tasks
        try:
            cursor.execute("SELECT id, title, description, status, assigned_to, due_date, priority FROM task")
            existing_data['tasks'] = cursor.fetchall()
            print(f"Found {len(existing_data['tasks'])} existing tasks")
        except sqlite3.OperationalError:
            print("No task table found in existing database")

    except Exception as e:
        print(f"Error reading existing data: {e}")
    finally:
        conn.close()

    return existing_data


def migrate_database():
    """Migrate the database to the new schema."""
    print("Starting database migration...")

    # Backup existing data
    existing_data = backup_existing_data()

    # Remove old database
    db_path = 'taskflow.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Old database removed")

    # Create Flask app context
    app = create_app()

    with app.app_context():
        # Create new tables
        db.create_all()
        print("New database schema created")

        if existing_data:
            # Migrate users
            user_id_mapping = {}
            for old_id, username, password in existing_data['users']:
                # Check if user already exists
                existing_user = User.query.filter_by(username=username).first()
                if not existing_user:
                    user = User(username=username)
                    user.set_password(password)  # This will hash the password
                    db.session.add(user)
                    db.session.flush()  # Get the new ID

                    # Create default swimlane for migrated user
                    default_swimlane = Swimlane(name='General', user_id=user.id)
                    db.session.add(default_swimlane)
                    db.session.flush()

                    user_id_mapping[old_id] = (user.id, default_swimlane.id)
                    print(f"Migrated user: {username}")
                else:
                    # Get existing user's default swimlane
                    default_swimlane = Swimlane.query.filter_by(user_id=existing_user.id, name='General').first()
                    if not default_swimlane:
                        default_swimlane = Swimlane(name='General', user_id=existing_user.id)
                        db.session.add(default_swimlane)
                        db.session.flush()
                    user_id_mapping[old_id] = (existing_user.id, default_swimlane.id)

            # Migrate tasks
            for task_data in existing_data['tasks']:
                task_id, title, description, status, assigned_to, due_date, priority = task_data

                # Map old status to new status
                status_mapping = {
                    'To Do': 'Backlog',
                    'Doing': 'In Progress',
                    'Done': 'Complete'
                }
                new_status = status_mapping.get(status, 'Backlog')

                # Assign to first user if no specific assignment
                if user_id_mapping:
                    user_id, swimlane_id = list(user_id_mapping.values())[0]

                    task = Task(
                        title=title or 'Untitled Task',
                        description=description or '',
                        status=new_status,
                        swimlane_id=swimlane_id,
                        user_id=user_id
                    )
                    db.session.add(task)
                    print(f"Migrated task: {title}")

            db.session.commit()
            print(
                f"Migration completed! Migrated {len(existing_data['users'])} users and {len(existing_data['tasks'])} tasks")
        else:
            print("No existing data to migrate")

    print("Database migration finished successfully!")


def create_sample_data():
    """Create some sample data for testing."""
    app = create_app()

    with app.app_context():
        # Create sample user
        if not User.query.filter_by(username='demo').first():
            demo_user = User(username='demo')
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.flush()

            # Create sample swimlanes
            swimlanes = [
                Swimlane(name='Frontend', user_id=demo_user.id),
                Swimlane(name='Backend', user_id=demo_user.id),
                Swimlane(name='Testing', user_id=demo_user.id)
            ]

            for swimlane in swimlanes:
                db.session.add(swimlane)

            db.session.flush()

            # Create sample tasks
            tasks = [
                Task(title='Design login page', description='Create wireframes and mockups',
                     status='Complete', swimlane_id=swimlanes[0].id, user_id=demo_user.id),
                Task(title='Implement authentication', description='Add Flask-Login integration',
                     status='In Progress', swimlane_id=swimlanes[1].id, user_id=demo_user.id),
                Task(title='Setup database models', description='Create User, Task, and Swimlane models',
                     status='Complete', swimlane_id=swimlanes[1].id, user_id=demo_user.id),
                Task(title='Write unit tests', description='Test all API endpoints',
                     status='Backlog', swimlane_id=swimlanes[2].id, user_id=demo_user.id),
            ]

            for task in tasks:
                db.session.add(task)

            db.session.commit()
            print("Sample data created!")
            print("Demo user created - Username: demo, Password: demo123")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--sample-data':
        create_sample_data()
    else:
        migrate_database()

        # Ask if user wants sample data
        response = input("\nWould you like to create sample data for testing? (y/n): ")
        if response.lower() in ['y', 'yes']:
            create_sample_data()
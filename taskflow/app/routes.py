from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Task, Swimlane
from . import db

main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def login():
    """Login page - now the default route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please fill in all fields')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password or not confirm_password:
            flash('Please fill in all fields')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create default swimlane
        default_swimlane = Swimlane(name='General', user_id=user.id)
        db.session.add(default_swimlane)
        db.session.commit()

        login_user(user)
        flash('Registration successful! Welcome to TaskFlow!')
        return redirect(url_for('main.dashboard'))

    return render_template('register.html')


@main.route('/logout')
@login_required
def logout():
    """Logout user and redirect to login page"""
    logout_user()
    flash('You have been logged out successfully')
    return redirect(url_for('main.login'))


@main.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - requires authentication"""
    swimlanes = Swimlane.query.filter_by(user_id=current_user.id).all()
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', swimlanes=swimlanes, tasks=tasks)


# API Routes for AJAX calls
@main.route('/api/swimlanes', methods=['GET', 'POST'])
@login_required
def api_swimlanes():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name', '').strip()

        if not name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400

        # Check if swimlane already exists for this user
        existing = Swimlane.query.filter_by(name=name, user_id=current_user.id).first()
        if existing:
            return jsonify({'success': False, 'error': 'Swimlane already exists'}), 400

        swimlane = Swimlane(name=name, user_id=current_user.id)
        db.session.add(swimlane)
        db.session.commit()

        return jsonify({'success': True, 'swimlane': swimlane.to_dict()})

    # GET request
    swimlanes = Swimlane.query.filter_by(user_id=current_user.id).all()
    return jsonify([s.to_dict() for s in swimlanes])


@main.route('/api/swimlanes/<int:swimlane_id>', methods=['DELETE'])
@login_required
def api_delete_swimlane(swimlane_id):
    swimlane = Swimlane.query.filter_by(id=swimlane_id, user_id=current_user.id).first()
    if not swimlane:
        return jsonify({'success': False, 'error': 'Swimlane not found'}), 404

    db.session.delete(swimlane)
    db.session.commit()

    return jsonify({'success': True})


@main.route('/api/tasks', methods=['GET', 'POST'])
@login_required
def api_tasks():
    if request.method == 'POST':
        from datetime import datetime

        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        swimlane_id = data.get('swimlane_id')
        priority = data.get('priority', 'Medium')
        due_date_str = data.get('due_date')

        if not title or not swimlane_id:
            return jsonify({'success': False, 'error': 'Title and swimlane are required'}), 400

        # Verify swimlane belongs to current user
        swimlane = Swimlane.query.filter_by(id=swimlane_id, user_id=current_user.id).first()
        if not swimlane:
            return jsonify({'success': False, 'error': 'Invalid swimlane'}), 400

        # Parse due date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid due date format'}), 400

        task = Task(
            title=title,
            description=description,
            swimlane_id=swimlane_id,
            user_id=current_user.id,
            status='Backlog',
            priority=priority,
            due_date=due_date
        )
        db.session.add(task)
        db.session.commit()

        return jsonify({'success': True, 'task': task.to_dict()})

    # GET request
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return jsonify([t.to_dict() for t in tasks])


@main.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
@login_required
def api_task(task_id):
    from datetime import datetime

    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404

    if request.method == 'PUT':
        data = request.get_json()

        if 'title' in data:
            task.title = data['title'].strip()
        if 'description' in data:
            task.description = data['description'].strip()
        if 'status' in data:
            if data['status'] in ['Backlog', 'In Progress', 'Complete']:
                task.status = data['status']
        if 'priority' in data:
            if data['priority'] in ['High', 'Medium', 'Low']:
                task.priority = data['priority']
        if 'due_date' in data:
            due_date_str = data['due_date']
            if due_date_str:
                try:
                    task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'success': False, 'error': 'Invalid due date format'}), 400
            else:
                task.due_date = None

        db.session.commit()
        return jsonify({'success': True, 'task': task.to_dict()})

    elif request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True})
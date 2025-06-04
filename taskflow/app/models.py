from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    swimlanes = db.relationship('Swimlane', backref='owner', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='creator', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Swimlane(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    tasks = db.relationship('Task', backref='swimlane', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Backlog')  # Backlog, In Progress, Complete
    priority = db.Column(db.String(10), default='Medium')  # High, Medium, Low
    due_date = db.Column(db.Date, nullable=True)
    swimlane_id = db.Column(db.Integer, db.ForeignKey('swimlane.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'swimlane_id': self.swimlane_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status != 'Complete':
            return self.due_date < datetime.now().date()
        return False

    @property
    def priority_color(self):
        """Get color for priority"""
        colors = {
            'High': '#ef4444',  # Red
            'Medium': '#f59e0b',  # Amber
            'Low': '#10b981'  # Green
        }
        return colors.get(self.priority, '#6b7280')
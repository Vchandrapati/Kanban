from app import create_app, db
from app.models import User, Swimlane, Task
from flask.cli import with_appcontext
import click

app = create_app()


@click.command(name='create_tables')
@with_appcontext
def create_tables():
    """Create database tables."""
    db.create_all()
    click.echo("Database tables created successfully.")


@click.command(name='create_user')
@click.argument('username')
@click.argument('password')
@with_appcontext
def create_user(username, password):
    """Create a new user."""
    if User.query.filter_by(username=username).first():
        click.echo(f"User '{username}' already exists.")
        return

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)

    # Create default swimlane
    default_swimlane = Swimlane(name='General', user_id=user.id)
    db.session.add(default_swimlane)

    db.session.commit()
    click.echo(f"User '{username}' created successfully with default swimlane.")


@click.command(name='reset_db')
@with_appcontext
def reset_db():
    """Drop and recreate all tables."""
    if click.confirm('This will delete all data. Are you sure?'):
        db.drop_all()
        db.create_all()
        click.echo("Database reset successfully.")


app.cli.add_command(create_tables)
app.cli.add_command(create_user)
app.cli.add_command(reset_db)

if __name__ == '__main__':
    app.run(debug=True)
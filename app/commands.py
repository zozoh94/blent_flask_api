"""Custom Flask CLI commands: database setup and test-data seeding.

Registered on the app in create_app, they are run with:
    flask --app app init-db
    flask --app app seed
"""

import click
from flask import Flask
from flask.cli import with_appcontext

from app.extensions import db
from app.models import User


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create every database table from the models."""
    db.create_all()
    click.echo("Database initialized.")


# Test accounts created by `seed`, with their plaintext passwords so the API can
# be tried out right away.
SEED_USERS = [
    {
        "email": "admin@digimarket.test",
        "name": "Admin",
        "role": "admin",
        "password": "AdminPass123",
    },
    {
        "email": "client@digimarket.test",
        "name": "Zoen Linhame",
        "role": "client",
        "password": "ClientPass123",
    },
]


@click.command("seed")
@with_appcontext
def seed_command():
    """Insert a small set of test users. Safe to re-run: existing ones are kept."""
    for spec in SEED_USERS:
        # Skip anyone already there, so the command is idempotent.
        if db.session.scalar(db.select(User).filter_by(email=spec["email"])):
            click.echo(f"- {spec['email']} already exists, skipped")
            continue

        user = User(email=spec["email"], name=spec["name"], role=spec["role"])
        user.password = spec["password"]
        db.session.add(user)
        click.echo(f"+ {spec['email']} ({spec['role']})")

    db.session.commit()
    click.echo("Seed complete.")


@click.command("grant-admin")
@click.option(
    "--email",
    prompt="Enter user email",
    help="Email of the user to grant admin privileges",
)
@with_appcontext
def grant_admin_command(email):
    """Grant admin privileges to a user."""
    user = db.session.scalar(db.select(User).filter_by(email=email))
    if user:
        user.role = "admin"
        db.session.commit()
        click.echo(f"Admin privileges granted to {email}.")
    else:
        click.echo("User not found.")


def register_commands(app: Flask) -> None:
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_command)
    app.cli.add_command(grant_admin_command)

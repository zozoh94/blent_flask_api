"""Custom Flask CLI commands: database setup and test-data seeding.

Registered on the app in create_app, they are run with:
    flask --app app init-db
    flask --app app seed
"""

import click
from flask import Flask
from flask.cli import with_appcontext

from app.extensions import db
from app.models import Order, OrderItem, Product, User


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


# Test catalog for the DigiMarket store (computer hardware).
SEED_PRODUCTS = [
    {
        "name": "Clavier mécanique RGB",
        "description": "Clavier mécanique à switches rouges, rétroéclairage RGB.",
        "category": "Périphériques",
        "price": 89.99,
        "stock": 40,
    },
    {
        "name": "Souris gaming sans fil",
        "description": "Souris optique 16000 DPI, sans fil, 6 boutons programmables.",
        "category": "Périphériques",
        "price": 49.99,
        "stock": 60,
    },
    {
        "name": 'Écran 27" 144 Hz',
        "description": "Moniteur 27 pouces QHD, dalle IPS, 144 Hz.",
        "category": "Écrans",
        "price": 299.00,
        "stock": 15,
    },
    {
        "name": "SSD NVMe 1 To",
        "description": "Disque SSD NVMe PCIe 4.0, 1 To, jusqu'à 7000 Mo/s.",
        "category": "Stockage",
        "price": 109.90,
        "stock": 80,
    },
]


# A few orders placed by the seed client, left pending on purpose: an order only
# consumes stock once an admin validates it, so seeding them as pending keeps the
# catalog stock consistent. Products are named here; their ids are resolved at
# insert time.
SEED_ORDERS = [
    {
        "shipping_address": "1 rue du Test, 75001 Paris",
        "items": [
            {"product": "Clavier mécanique RGB", "quantity": 1},
            {"product": "Souris gaming sans fil", "quantity": 2},
        ],
    },
    {
        "shipping_address": "1 rue du Test, 75001 Paris",
        "items": [
            {"product": 'Écran 27" 144 Hz', "quantity": 1},
        ],
    },
]


@click.command("seed")
@with_appcontext
def seed_command():
    """Insert a small set of test users and products. Safe to re-run."""
    for spec in SEED_USERS:
        # Skip anyone already there, so the command is idempotent.
        if db.session.scalar(db.select(User).filter_by(email=spec["email"])):
            click.echo(f"- {spec['email']} already exists, skipped")
            continue

        user = User(email=spec["email"], name=spec["name"], role=spec["role"])
        user.password = spec["password"]
        db.session.add(user)
        click.echo(f"+ {spec['email']} ({spec['role']})")

    for spec in SEED_PRODUCTS:
        # Products have no unique column, so guard on the name to stay idempotent.
        if db.session.scalar(db.select(Product).filter_by(name=spec["name"])):
            click.echo(f"- {spec['name']} already exists, skipped")
            continue

        db.session.add(Product(**spec))
        click.echo(f"+ {spec['name']} ({spec['category']})")

    # Orders come last: they need their client and products to exist first.
    client = db.session.scalar(
        db.select(User).filter_by(email="client@digimarket.test")
    )
    if db.session.scalar(db.select(Order).limit(1)):
        # Any existing order means we have already seeded: stay idempotent.
        click.echo("- orders already exist, skipped")
    elif client is None:
        click.echo("- no seed client, orders skipped")
    else:
        for spec in SEED_ORDERS:
            # Resolve each named product and snapshot its price, as the API does.
            items = [
                OrderItem(
                    product_id=product.id,
                    quantity=line["quantity"],
                    unit_price=product.price,
                )
                for line in spec["items"]
                if (
                    product := db.session.scalar(
                        db.select(Product).filter_by(name=line["product"])
                    )
                )
            ]
            order = Order(
                user_id=client.id,
                shipping_address=spec["shipping_address"],
                items=items,
            )
            db.session.add(order)
            click.echo(f"+ order for {client.email} ({len(items)} item(s))")

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

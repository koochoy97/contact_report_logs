"""Seed script: add accounts and clients to the database.

Usage:
    python -m app.seed

Edit the ACCOUNTS list below with your Reply.io credentials and workspaces.
"""
from app.db import SessionLocal
from app.migrate import run_migrations
from app.models import Account, Client
from app.utils.crypto import encrypt

# ──────────────────────────────────────────────
# Edit this list with your accounts and clients
# ──────────────────────────────────────────────
ACCOUNTS = [
    {
        "email": "user@example.com",
        "password": "plain_password_here",
        "label": "Main Account",
        "clients": [
            {"team_id": 123456, "display_name": "Client A"},
            {"team_id": 789012, "display_name": "Client B"},
        ],
    },
    # Add more accounts...
]


def seed():
    run_migrations()
    session = SessionLocal()

    for acc_data in ACCOUNTS:
        existing = session.query(Account).filter_by(email=acc_data["email"]).first()
        if existing:
            print(f"[seed] Cuenta ya existe: {acc_data['email']}, actualizando...")
            account = existing
            account.password_encrypted = encrypt(acc_data["password"])
            account.label = acc_data.get("label")
        else:
            account = Account(
                email=acc_data["email"],
                password_encrypted=encrypt(acc_data["password"]),
                label=acc_data.get("label"),
            )
            session.add(account)
            session.flush()

        for cl_data in acc_data.get("clients", []):
            existing_client = (
                session.query(Client)
                .filter_by(account_id=account.id, team_id=cl_data["team_id"])
                .first()
            )
            if existing_client:
                existing_client.display_name = cl_data["display_name"]
                print(f"  [seed] Cliente actualizado: {cl_data['display_name']}")
            else:
                client = Client(
                    account_id=account.id,
                    team_id=cl_data["team_id"],
                    display_name=cl_data["display_name"],
                )
                session.add(client)
                print(f"  [seed] Cliente creado: {cl_data['display_name']}")

    session.commit()
    session.close()
    print("[seed] Seed completado")


if __name__ == "__main__":
    seed()

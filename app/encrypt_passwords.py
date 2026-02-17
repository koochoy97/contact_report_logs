"""Encrypt all plain-text reply_password values in core.clientes.

Usage:
    python3 -m app.encrypt_passwords

Reads reply_password from core.clientes, encrypts any that aren't
already Fernet-encrypted (don't start with 'gAAAAA'), and updates them in place.
"""
from sqlalchemy import text

from app.db import engine
from app.utils.crypto import encrypt


def encrypt_passwords():
    with engine.begin() as conn:
        rows = conn.execute(text(
            "SELECT id, cliente, reply_password FROM core.clientes "
            "WHERE reply_password IS NOT NULL AND reply_password != ''"
        )).fetchall()

        updated = 0
        for row in rows:
            client_id, name, password = row

            # Skip already encrypted values
            if password.startswith("gAAAAA"):
                print(f"  [{name}] ya encriptado, saltando")
                continue

            encrypted = encrypt(password)
            conn.execute(
                text("UPDATE core.clientes SET reply_password = :enc WHERE id = :id"),
                {"enc": encrypted, "id": client_id},
            )
            print(f"  [{name}] encriptado OK")
            updated += 1

    print(f"\n[encrypt] {updated} contraseñas encriptadas")


if __name__ == "__main__":
    encrypt_passwords()

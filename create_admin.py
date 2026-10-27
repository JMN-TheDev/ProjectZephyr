"""Create the first admin account (run after importing schema.sql)."""
import getpass

from werkzeug.security import generate_password_hash
from app import query


def main():
    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password (minimum 8 characters): ")
    if not name or not email or len(password) < 8:
        raise SystemExit("Name and email are required; password must be at least 8 characters.")
    if query("SELECT id FROM users WHERE email=%s", (email,), one=True):
        raise SystemExit("That email is already registered.")
    query("INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,'admin')",
          (name, email, generate_password_hash(password)), commit=True)
    print(f"Admin account created for {email}.")


if __name__ == "__main__":
    main()

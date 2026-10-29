"""Basic menu-driven inventory and ordering program for Python IDLE.

Before running: install mysql-connector-python, execute simple_inventory.sql,
and edit the DB_CONFIG values below to match your local MySQL account.
"""
import hashlib
import secrets
from decimal import Decimal, InvalidOperation

import mysql.connector

# Change these settings to match the MySQL server where the SQL file was run.
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "item_inventory_simple",
}


def connect():
    return mysql.connector.connect(**DB_CONFIG)


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000)
    return salt + "$" + digest.hex()


def password_matches(password, saved_hash):
    salt, expected = saved_hash.split("$", 1)
    actual = password_hash(password, salt).split("$", 1)[1]
    return secrets.compare_digest(actual, expected)


def ask_int(prompt, minimum=0):
    while True:
        try:
            value = int(input(prompt).strip())
            if value < minimum:
                print("Enter a number of at least", minimum)
            else:
                return value
        except ValueError:
            print("Enter a whole number.")


def ask_price(prompt):
    while True:
        try:
            value = Decimal(input(prompt).strip()).quantize(Decimal("0.01"))
            if value < 0:
                print("Price cannot be negative.")
            else:
                return value
        except InvalidOperation:
            print("Enter a valid price, for example 12.50.")


def create_first_admin():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cur.fetchone()[0] != 0:
        conn.close()
        print("An admin already exists. Ask an admin to create accounts.")
        return
    print("First-run setup: create the initial administrator.")
    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = input("Admin password (8+ characters): ")
    if not name or not email or len(password) < 8:
        conn.close()
        print("Name, email, and a password of at least 8 characters are required.")
        return
    try:
        cur.execute("INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,'admin')",
                    (name, email, password_hash(password)))
        conn.commit()
        print("Admin account created. You can now sign in.")
    except mysql.connector.IntegrityError:
        conn.rollback()
        print("That email is already in use.")
    finally:
        conn.close()


def register_customer():
    name = input("Your name: ").strip()
    email = input("Email: ").strip().lower()
    password = input("Password (8+ characters): ")
    if not name or not email or len(password) < 8:
        print("Name and email are required; password must be at least 8 characters.")
        return
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,'customer')",
                    (name, email, password_hash(password)))
        conn.commit()
        print("Customer account created. Sign in from the main menu.")
    except mysql.connector.IntegrityError:
        conn.rollback()
        print("That email is already registered.")
    finally:
        conn.close()


def sign_in():
    email = input("Email: ").strip().lower()
    password = input("Password: ")
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id,name,password_hash,role FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    conn.close()
    if not user or not password_matches(password, user[2]):
        print("Email or password is incorrect.")
        return
    print("\nWelcome,", user[1])
    if user[3] == "admin":
        admin_menu(user[0])
    else:
        customer_menu(user[0])


def list_products(active_only=True):
    conn = connect()
    cur = conn.cursor()
    if active_only:
        cur.execute("SELECT id,name,price,stock FROM products WHERE active=TRUE ORDER BY name")
    else:
        cur.execute("SELECT id,name,price,stock,active FROM products ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("No products found.")
    for row in rows:
        state = "" if active_only else (" | active" if row[4] else " | hidden")
        print("ID {} | {} | ${:.2f} | {} in stock{}".format(row[0], row[1], row[2], row[3], state))


def add_product():
    name = input("Product name: ").strip()
    if not name:
        print("Product name is required.")
        return
    price = ask_price("Price: $")
    stock = ask_int("Starting stock: ")
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name,price,stock) VALUES (%s,%s,%s)", (name, price, stock))
    conn.commit()
    conn.close()
    print("Product added.")


def change_stock():
    list_products(active_only=False)
    product_id = ask_int("Product ID to update: ", 1)
    stock = ask_int("New stock quantity: ")
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE products SET stock=%s WHERE id=%s", (stock, product_id))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    print("Stock updated." if changed else "Product ID not found.")


def toggle_product():
    list_products(active_only=False)
    product_id = ask_int("Product ID to show/hide: ", 1)
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE products SET active=NOT active WHERE id=%s", (product_id,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    print("Product visibility changed." if changed else "Product ID not found.")


def show_orders():
    conn = connect()
    cur = conn.cursor(dictionary=True)
    cur.execute("""SELECT o.id,o.user_id,u.name,o.total,o.status,o.created_at
                   FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC""")
    orders = cur.fetchall()
    if not orders:
        print("No orders yet.")
    for order in orders:
        print("\nOrder #{} | {} ({}) | ${:.2f} | {} | {}".format(
            order["id"], order["name"], order["user_id"], order["total"], order["status"], order["created_at"]))
        cur.execute("SELECT product_name,quantity,unit_price FROM order_items WHERE order_id=%s", (order["id"],))
        for item in cur.fetchall():
            print("  - {} x{} @ ${:.2f}".format(item["product_name"], item["quantity"], item["unit_price"]))
    conn.close()


def change_order_status():
    show_orders()
    order_id = ask_int("Order ID to update: ", 1)
    print("1. Pending  2. Processing  3. Completed  4. Cancelled")
    statuses = {"1": "pending", "2": "processing", "3": "completed", "4": "cancelled"}
    choice = input("New status: ").strip()
    if choice not in statuses:
        print("Choose 1, 2, 3, or 4.")
        return
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("SELECT status FROM orders WHERE id=%s FOR UPDATE", (order_id,))
        current = cur.fetchone()
        if not current:
            conn.rollback()
            print("Order ID not found.")
            return
        new_status = statuses[choice]
        if current[0] == "cancelled" and new_status != "cancelled":
            conn.rollback()
            print("A cancelled order cannot be reopened.")
            return
        if new_status == "cancelled" and current[0] != "cancelled":
            cur.execute("SELECT product_id,quantity FROM order_items WHERE order_id=%s", (order_id,))
            for product_id, quantity in cur.fetchall():
                if product_id is not None:
                    cur.execute("UPDATE products SET stock=stock+%s WHERE id=%s", (quantity, product_id))
        cur.execute("UPDATE orders SET status=%s WHERE id=%s", (new_status, order_id))
        conn.commit()
        print("Order updated." + (" Stock restored." if new_status == "cancelled" else ""))
    except mysql.connector.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def admin_menu(admin_id):
    while True:
        print("\n=== ADMIN MENU ===")
        print("1. List products\n2. Add product\n3. Change stock\n4. Show all orders")
        print("5. Change order status\n6. Show/hide product\n0. Sign out")
        choice = input("Choose: ").strip()
        try:
            if choice == "1": list_products(active_only=False)
            elif choice == "2": add_product()
            elif choice == "3": change_stock()
            elif choice == "4": show_orders()
            elif choice == "5": change_order_status()
            elif choice == "6": toggle_product()
            elif choice == "0": return
            else: print("Choose one of the listed options.")
        except mysql.connector.Error as exc:
            print("Database operation failed:", exc)


def customer_orders(user_id):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id,total,status,created_at FROM orders WHERE user_id=%s ORDER BY id DESC", (user_id,))
    orders = cur.fetchall()
    if not orders:
        print("You have no orders yet.")
    for order in orders:
        print("\nOrder #{} | ${:.2f} | {} | {}".format(order["id"], order["total"], order["status"], order["created_at"]))
        cur.execute("SELECT product_name,quantity,unit_price FROM order_items WHERE order_id=%s", (order["id"],))
        for item in cur.fetchall():
            print("  - {} x{} @ ${:.2f}".format(item["product_name"], item["quantity"], item["unit_price"]))
    conn.close()


def place_order(user_id):
    list_products()
    product_id = ask_int("Product ID to order: ", 1)
    quantity = ask_int("Quantity: ", 1)
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id,name,price,stock,active FROM products WHERE id=%s FOR UPDATE", (product_id,))
        product = cur.fetchone()
        if not product or not product["active"]:
            print("Product is unavailable.")
            conn.rollback()
            return
        if product["stock"] < quantity:
            print("Not enough stock. Available:", product["stock"])
            conn.rollback()
            return
        total = product["price"] * quantity
        cur.execute("INSERT INTO orders (user_id,total) VALUES (%s,%s)", (user_id, total))
        order_id = cur.lastrowid
        cur.execute("INSERT INTO order_items (order_id,product_id,product_name,quantity,unit_price) VALUES (%s,%s,%s,%s,%s)",
                    (order_id, product["id"], product["name"], quantity, product["price"]))
        cur.execute("UPDATE products SET stock=stock-%s WHERE id=%s", (quantity, product_id))
        conn.commit()
        print("Order #{} placed. Total: ${:.2f}".format(order_id, total))
    except mysql.connector.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


def customer_menu(user_id):
    while True:
        print("\n=== CUSTOMER MENU ===")
        print("1. Browse products\n2. Place an order\n3. My order history\n0. Sign out")
        choice = input("Choose: ").strip()
        try:
            if choice == "1": list_products()
            elif choice == "2": place_order(user_id)
            elif choice == "3": customer_orders(user_id)
            elif choice == "0": return
            else: print("Choose one of the listed options.")
        except mysql.connector.Error as exc:
            print("Database operation failed:", exc)


def main():
    while True:
        print("\n=== SIMPLE INVENTORY MANAGEMENT ===")
        print("1. Sign in\n2. Register customer account\n3. Create first admin (setup only)\n0. Exit")
        choice = input("Choose: ").strip()
        try:
            if choice == "1": sign_in()
            elif choice == "2": register_customer()
            elif choice == "3": create_first_admin()
            elif choice == "0":
                print("Goodbye.")
                break
            else: print("Choose one of the listed options.")
        except mysql.connector.Error as exc:
            print("Cannot connect to MySQL. Check DB_CONFIG and run simple_inventory.sql first.")
            print("Details:", exc)


if __name__ == "__main__":
    main()

import os
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "replace-this-with-a-random-secret")


def db_connection():
    options = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "item_inventory"),
    }
    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca:
        options.update(ssl_ca=ssl_ca, ssl_verify_cert=True, ssl_verify_identity=True)
    return mysql.connector.connect(**options)


def query(sql, params=(), one=False, commit=False):
    conn = db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        if commit:
            conn.commit()
            return cur.lastrowid
        return cur.fetchone() if one else cur.fetchall()
    finally:
        conn.close()


def rollback_quietly(conn):
    if conn:
        try:
            conn.rollback()
        except mysql.connector.Error:
            app.logger.exception("Could not roll back database transaction")


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please sign in to continue.", "warning")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You do not have access to that page.", "error")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.context_processor
def inject_cart_count():
    cart = session.get("cart", {})
    return {"cart_count": sum(int(v) for v in cart.values()), "now_year": datetime.now().year}


@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    if search:
        products = query("SELECT * FROM products WHERE active=1 AND (name LIKE %s OR category LIKE %s OR description LIKE %s) ORDER BY name",
                         (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        products = query("SELECT * FROM products WHERE active=1 ORDER BY created_at DESC")
    return render_template("index.html", products=products, search=search)


@app.route("/simple-project")
def simple_project():
    root = Path(__file__).resolve().parent
    menu_code = (root / "simple_inventory.py").read_text(encoding="utf-8")
    sql_code = (root / "simple_inventory.sql").read_text(encoding="utf-8")
    return render_template("simple_project.html", menu_code=menu_code, sql_code=sql_code)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password with at least 8 characters.", "error")
        elif query("SELECT id FROM users WHERE email=%s", (email,), one=True):
            flash("An account with that email already exists.", "error")
        else:
            query("INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,'customer')",
                  (name, email, generate_password_hash(password)), commit=True)
            flash("Account created. You can now sign in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = query("SELECT * FROM users WHERE email=%s", (email,), one=True)
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            cart = session.get("cart", {})
            session.clear()
            session.update(user_id=user["id"], name=user["name"], role=user["role"], cart=cart)
            flash(f"Welcome back, {user['name']}.", "success")
            return redirect(url_for("admin_dashboard" if user["role"] == "admin" else "index"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))


@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    product = query("SELECT id,name,stock FROM products WHERE id=%s AND active=1", (product_id,), one=True)
    if not product:
        flash("That item is unavailable.", "error")
    else:
        cart = session.get("cart", {})
        key = str(product_id)
        if int(cart.get(key, 0)) >= product["stock"]:
            flash("There is not enough stock to add another.", "warning")
        else:
            cart[key] = int(cart.get(key, 0)) + 1
            session["cart"] = cart
            flash(f"{product['name']} added to your basket.", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/cart")
def cart():
    cart_data = session.get("cart", {})
    ids = [int(k) for k, v in cart_data.items() if int(v) > 0]
    products = query("SELECT * FROM products WHERE id IN (" + ",".join(["%s"] * len(ids)) + ")", tuple(ids)) if ids else []
    items, total = [], Decimal("0")
    for product in products:
        qty = min(int(cart_data.get(str(product["id"]), 1)), product["stock"])
        line_total = product["price"] * qty
        total += line_total
        items.append({"product": product, "quantity": qty, "line_total": line_total})
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/update")
def update_cart():
    cart_data = session.get("cart", {})
    for key, value in request.form.items():
        if key.startswith("qty_"):
            product_id = key[4:]
            try:
                qty = max(0, min(int(value), 999))
            except ValueError:
                qty = 0
            if qty:
                cart_data[product_id] = qty
            else:
                cart_data.pop(product_id, None)
    session["cart"] = cart_data
    flash("Basket updated.", "success")
    return redirect(url_for("cart"))


@app.post("/checkout")
@login_required("customer")
def checkout():
    cart_data = session.get("cart", {})
    if not cart_data:
        flash("Your basket is empty.", "warning")
        return redirect(url_for("cart"))
    conn = None
    try:
        conn = db_connection()
        cur = conn.cursor(dictionary=True)
        total = Decimal("0")
        checked = []
        for pid, qty in cart_data.items():
            cur.execute("SELECT id,name,price,stock,active FROM products WHERE id=%s FOR UPDATE", (int(pid),))
            product = cur.fetchone()
            qty = int(qty)
            if not product or not product["active"] or product["stock"] < qty:
                raise ValueError("One or more items changed availability. Please update your basket.")
            total += product["price"] * qty
            checked.append((product, qty))
        cur.execute("INSERT INTO orders (user_id,total,status) VALUES (%s,%s,'pending')", (session["user_id"], total))
        order_id = cur.lastrowid
        for product, qty in checked:
            cur.execute("INSERT INTO order_items (order_id,product_id,product_name,quantity,unit_price) VALUES (%s,%s,%s,%s,%s)",
                        (order_id, product["id"], product["name"], qty, product["price"]))
            cur.execute("UPDATE products SET stock=stock-%s WHERE id=%s", (qty, product["id"]))
        conn.commit()
        session["cart"] = {}
        return render_template(
            "order_confirmation.html",
            order_id=order_id,
            total=total,
            items=checked,
        )
    except ValueError as exc:
        rollback_quietly(conn)
        flash(str(exc), "warning")
        return redirect(url_for("cart"))
    except mysql.connector.Error:
        rollback_quietly(conn)
        app.logger.exception("Database error while placing order")
        flash("We could not place your order right now. Your basket is still saved; please try again.", "error")
        return redirect(url_for("cart"))
    except Exception:
        rollback_quietly(conn)
        app.logger.exception("Unexpected error while placing order")
        flash("Something went wrong while placing your order. Your basket is still saved; please try again.", "error")
        return redirect(url_for("cart"))
    finally:
        if conn:
            conn.close()


@app.route("/orders")
@login_required("customer")
def my_orders():
    orders = query("SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC", (session["user_id"],))
    for order in orders:
        order["items"] = query("SELECT * FROM order_items WHERE order_id=%s", (order["id"],))
    return render_template("orders.html", orders=orders)


@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    products = query("SELECT * FROM products ORDER BY active DESC,name")
    stats = query("SELECT (SELECT COUNT(*) FROM products WHERE active=1) AS products, (SELECT COALESCE(SUM(stock),0) FROM products WHERE active=1) AS units, (SELECT COUNT(*) FROM orders WHERE status='pending') AS pending_orders, (SELECT COUNT(*) FROM products WHERE active=1 AND stock<=5) AS low_stock", one=True)
    orders = query("SELECT o.*,u.name AS customer_name FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC")
    for order in orders:
        order["items"] = query("SELECT * FROM order_items WHERE order_id=%s", (order["id"],))
    return render_template("admin.html", products=products, stats=stats, orders=orders)


@app.post("/admin/products/save")
@login_required("admin")
def save_product():
    form = request.form
    name, category = form.get("name", "").strip(), form.get("category", "").strip()
    try:
        price, stock = Decimal(form.get("price", "")), int(form.get("stock", ""))
        if not name or price < 0 or stock < 0:
            raise ValueError
    except (ValueError, InvalidOperation):
        flash("Enter a product name, a valid non-negative price and stock quantity.", "error")
        return redirect(url_for("admin_dashboard"))
    pid = form.get("id", "").strip()
    values = (name, category, form.get("description", "").strip(), price, stock)
    if pid:
        query("UPDATE products SET name=%s,category=%s,description=%s,price=%s,stock=%s WHERE id=%s", values + (pid,), commit=True)
        flash("Product updated.", "success")
    else:
        query("INSERT INTO products (name,category,description,price,stock) VALUES (%s,%s,%s,%s,%s)", values, commit=True)
        flash("Product added.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/products/<int:product_id>/toggle")
@login_required("admin")
def toggle_product(product_id):
    query("UPDATE products SET active=IF(active=1,0,1) WHERE id=%s", (product_id,), commit=True)
    flash("Product visibility updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/orders/<int:order_id>/status")
@login_required("admin")
def update_order_status(order_id):
    status = request.form.get("status")
    if status not in ("pending", "processing", "completed", "cancelled"):
        flash("Invalid order status.", "error")
    else:
        conn = db_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT status FROM orders WHERE id=%s FOR UPDATE", (order_id,))
            order = cur.fetchone()
            if not order:
                flash("Order not found.", "error")
            elif order["status"] == "cancelled" and status != "cancelled":
                flash("A cancelled order cannot be reopened. Create a new order if needed.", "warning")
            else:
                if status == "cancelled" and order["status"] != "cancelled":
                    cur.execute("SELECT product_id,quantity FROM order_items WHERE order_id=%s", (order_id,))
                    for item in cur.fetchall():
                        if item["product_id"] is not None:
                            cur.execute("UPDATE products SET stock=stock+%s WHERE id=%s",
                                        (item["quantity"], item["product_id"]))
                cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
                conn.commit()
                flash("Order status updated." + (" Stock has been restored." if status == "cancelled" else ""), "success")
        except mysql.connector.Error:
            rollback_quietly(conn)
            app.logger.exception("Database error while updating order status")
            flash("Could not update this order. Please try again.", "error")
        finally:
            conn.close()
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "0") == "1")

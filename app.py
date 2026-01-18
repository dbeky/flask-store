from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"
DB_NAME = "store.db"

# ---------- Database ----------
def db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    con = db()
    c = con.cursor()
    # Users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)
    # Products
    c.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER
    )
    """)
    # Orders
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        product TEXT,
        qty INTEGER
    )
    """)

    # Admin default
    c.execute(
        "INSERT OR IGNORE INTO users(username,password,role) VALUES (?,?,?)",
        ("admin","admin123","admin")
    )
    con.commit()
    con.close()

init_db()

# ---------- Login ----------
@app.route("/", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        con = db()
        c = con.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (u,p))
        user = c.fetchone()
        con.close()
        if user:
            session["user"] = u
            session["role"] = user[0]
            return redirect("/dashboard")
        else:
            error = "Wrong username or password"
    return render_template("login.html", error=error)

# ---------- Dashboard ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# ---------- Admin Dashboard ----------
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return "Forbidden", 403
    con = db()
    c = con.cursor()
    users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    products = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    con.close()
    return render_template(
        "admin_dashboard.html",
        users=users,
        products=products,
        orders=orders
    )

# ---------- Products ----------
@app.route("/products", methods=["GET","POST"])
def products():
    if "user" not in session:
        return redirect("/")
    con = db()
    c = con.cursor()
    # Admin adds product
    if request.method == "POST" and session.get("role") == "admin":
        c.execute(
            "INSERT INTO products(name,price,stock) VALUES (?,?,?)",
            (
                request.form["name"],
                request.form["price"],
                request.form["stock"]
            )
        )
        con.commit()
    items = c.execute("SELECT * FROM products").fetchall()
    con.close()
    return render_template("products.html", items=items)

# ---------- Orders ----------
@app.route("/orders", methods=["GET","POST"])
def orders():
    if "user" not in session:
        return redirect("/")
    con = db()
    c = con.cursor()
    # Admin sees all, user sees only his
    if request.method == "POST":
        product_id = request.form["product"]
        qty = int(request.form["qty"])
        product_name = c.execute("SELECT name FROM products WHERE id=?", (product_id,)).fetchone()[0]
        c.execute("INSERT INTO orders(user,product,qty) VALUES (?,?,?)",
                  (session["user"], product_name, qty))
        con.commit()
        # Reduce stock
        c.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, product_id))
        con.commit()
    if session.get("role") == "admin":
        data = c.execute("SELECT * FROM orders").fetchall()
    else:
        data = c.execute("SELECT * FROM orders WHERE user=?", (session["user"],)).fetchall()
    products = c.execute("SELECT * FROM products WHERE stock>0").fetchall()
    con.close()
    return render_template("orders.html", orders=data, products=products)

# ---------- Logout ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- Run ----------
if __name__ == "__main__":
   import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )


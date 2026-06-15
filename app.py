from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = "database.db"

# -----------------------------
# Database
# -----------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS menu(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        price REAL,
        available INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_no INTEGER,
        total REAL,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        item_name TEXT,
        quantity INTEGER,
        price REAL
    )
    """)

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM menu")
    count = cur.fetchone()[0]

    if count == 0:
        items = [
            ("Veg Burger", "Mains", 120, 1),
            ("Pizza", "Mains", 250, 1),
            ("French Fries", "Starters", 90, 1),
            ("Coke", "Drinks", 50, 1),
            ("Coffee", "Drinks", 60, 1)
        ]

        cur.executemany(
            "INSERT INTO menu(name,category,price,available) VALUES(?,?,?,?)",
            items
        )
        conn.commit()

    conn.close()
# -----------------------------
# Home Page
# -----------------------------

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/menu")
def menu():

    table_no = request.args.get("table_no")

    conn = get_db()

    items = conn.execute(
        "SELECT * FROM menu WHERE available=1"
    ).fetchall()

    conn.close()

    return render_template(
        "menu.html",
        items=items,
        table_no=table_no
    )


# -----------------------------
# Place Order
# -----------------------------

@app.route("/place_order", methods=["POST"])
def place_order():

    table_no = request.form.get("table_no")

    conn = get_db()

    menu_items = conn.execute(
        "SELECT * FROM menu WHERE available=1"
    ).fetchall()

    total = 0
    order_data = []

    for item in menu_items:
        qty = int(request.form.get(f"qty_{item['id']}", 0))

        if qty > 0:
            subtotal = qty * item["price"]
            total += subtotal

            order_data.append(
                (item["name"], qty, item["price"])
            )

    cur = conn.cursor()

    cur.execute("""
    INSERT INTO orders(table_no,total,status)
    VALUES(?,?,?)
    """, (table_no, total, "Placed"))

    order_id = cur.lastrowid

    for name, qty, price in order_data:
        cur.execute("""
        INSERT INTO order_items
        (order_id,item_name,quantity,price)
        VALUES(?,?,?,?)
        """, (order_id, name, qty, price))

    conn.commit()
    conn.close()

    return redirect(url_for(
    "bill",
    order_id=order_id
))



# -----------------------------
# Order Status
# -----------------------------

@app.route("/order/<int:order_id>")
def order_status(order_id):

    conn = get_db()

    order = conn.execute(
        "SELECT * FROM orders WHERE id=?",
        (order_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "order_status.html",
        order=order
    )


# -----------------------------
# Kitchen Dashboard
# -----------------------------

@app.route("/kitchen")
def kitchen():

    conn = get_db()

    orders = conn.execute(
        "SELECT * FROM orders"
    ).fetchall()

    conn.close()

    return render_template(
        "kitchen.html",
        orders=orders
    )

@app.route("/update_status/<int:order_id>")
def update_status(order_id):

    conn = get_db()

    order = conn.execute(
        "SELECT * FROM orders WHERE id=?",
        (order_id,)
    ).fetchone()

    if order["status"] == "Placed":
        new_status = "Cooking"

    elif order["status"] == "Cooking":
        new_status = "Served"

    else:
        new_status = "Served"

    conn.execute(
        "UPDATE orders SET status=? WHERE id=?",
        (new_status, order_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("kitchen"))

# -----------------------------
# Admin Dashboard
# -----------------------------

@app.route("/admin")
def admin():

    conn = get_db()

    items = conn.execute(
        "SELECT * FROM menu"
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        items=items
    )

@app.route("/add_item", methods=["POST"])
def add_item():

    name = request.form["name"]
    category = request.form["category"]
    price = request.form["price"]

    conn = get_db()

    conn.execute("""
    INSERT INTO menu
    (name,category,price,available)
    VALUES(?,?,?,1)
    """, (name, category, price))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))
@app.route("/bill/<int:order_id>")
def bill(order_id):

    conn = get_db()

    order = conn.execute(
        "SELECT * FROM orders WHERE id=?",
        (order_id,)
    ).fetchone()

    items = conn.execute(
        "SELECT * FROM order_items WHERE order_id=?",
        (order_id,)
    ).fetchall()

    conn.close()

    return render_template(
    "bill.html",
    order=order,
    items=items
)

# -----------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
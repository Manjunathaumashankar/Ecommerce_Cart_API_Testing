import os
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)

# Database file path (configurable via environment variable)
DATABASE = os.environ.get("ECOMMERCE_DB", "ecommerce.db")


def get_db_connection():
    """Connect to the SQLite database and enable dictionary-like row access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """
    Creates necessary tables and seeds default products & discount coupons
    if they do not exist yet.
    """
    conn = get_db_connection()

    # 1. Products table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    # 2. Cart table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            product_id INTEGER PRIMARY KEY,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # 3. Coupons table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            code TEXT PRIMARY KEY,
            discount_type TEXT NOT NULL,  -- 'percent' or 'flat'
            discount_value REAL NOT NULL,
            min_order_value REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1   -- 1 for active, 0 for inactive/expired
        )
    """)

    # 4. Active Cart Coupon table (holds single applied coupon at any time)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cart_coupon (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            coupon_code TEXT NOT NULL,
            FOREIGN KEY (coupon_code) REFERENCES coupons(code)
        )
    """)

    # 5. Orders table (includes discount tracking)
    cols = [col[1] for col in conn.execute("PRAGMA table_info(orders)").fetchall()]
    if 'subtotal' not in cols:
        conn.execute("DROP TABLE IF EXISTS order_items")
        conn.execute("DROP TABLE IF EXISTS orders")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtotal REAL NOT NULL,
            discount_amount REAL DEFAULT 0.0,
            applied_coupon TEXT,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. Order items breakdown table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)

    # Seed products if empty
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO products (id, name, price, stock) VALUES (?, ?, ?, ?)",
            [
                (1, "Laptop", 55000.0, 10),
                (2, "Smartphone", 20000.0, 15),
                (3, "Headphones", 1500.0, 25),
                (4, "Keyboard", 800.0, 20),
                (5, "Mouse", 500.0, 30)
            ]
        )

    # Seed coupons if empty
    coupon_count = conn.execute("SELECT COUNT(*) FROM coupons").fetchone()[0]
    if coupon_count == 0:
        conn.executemany(
            "INSERT INTO coupons (code, discount_type, discount_value, min_order_value, is_active) VALUES (?, ?, ?, ?, ?)",
            [
                ("SAVE10", "percent", 10.0, 1000.0, 1),    # 10% off for order >= 1000
                ("FLAT500", "flat", 500.0, 2000.0, 1),      # Flat 500 off for order >= 2000
                ("MEGA20", "percent", 20.0, 10000.0, 1),   # 20% off for order >= 10000
                ("EXPIRED50", "percent", 50.0, 500.0, 0)   # Inactive/expired coupon for testing
            ]
        )

    conn.commit()
    conn.close()


# Custom JSON error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ==========================================================
# 1. HOME & HEALTH CHECK API
# ==========================================================
@app.route('/', methods=['GET'])
def home():
    """Returns API service status and list of available endpoints."""
    return jsonify({
        "message": "Welcome to E-commerce Shopping Cart API",
        "status": "API is running successfully",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /",
            "products": "GET /products, GET /products/<id>",
            "cart": "GET /cart, POST /cart, PUT /cart/<id>, DELETE /cart/<id>, DELETE /cart",
            "coupons": "GET /coupons, POST /cart/apply-coupon, DELETE /cart/coupon",
            "checkout": "POST /cart/checkout",
            "orders": "GET /orders, GET /orders/<id>",
            "reset": "POST /reset"
        }
    }), 200


# ==========================================================
# 2. PRODUCT CATALOG APIS
# ==========================================================
@app.route('/products', methods=['GET'])
def get_products():
    """Retrieve all available products in inventory."""
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(product) for product in products]), 200


@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Retrieve a single product by its unique ID."""
    conn = get_db_connection()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    conn.close()

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(dict(product)), 200


# ==========================================================
# 3. SHOPPING CART APIS
# ==========================================================
@app.route('/cart', methods=['POST'])
def add_to_cart():
    """
    Add a product to the shopping cart.
    Validates payload format, positive integers, product existence, and available stock.
    """
    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400

    if 'product_id' not in data or 'quantity' not in data:
        return jsonify({"error": "Product ID and quantity are required"}), 400

    product_id = data['product_id']
    quantity = data['quantity']

    # Type & boundary validation
    if type(product_id) is not int or type(quantity) is not int or product_id <= 0 or quantity <= 0:
        return jsonify({"error": "Product ID and quantity must be positive integers"}), 400

    conn = get_db_connection()

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()

    if product is None:
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    existing = conn.execute(
        "SELECT quantity FROM cart WHERE product_id = ?", (product_id,)
    ).fetchone()

    current_quantity = existing['quantity'] if existing else 0

    if current_quantity + quantity > product['stock']:
        conn.close()
        return jsonify({
            "error": "Insufficient stock",
            "available_stock": product['stock'],
            "current_in_cart": current_quantity,
            "requested_addition": quantity
        }), 400

    if existing:
        conn.execute(
            "UPDATE cart SET quantity = ? WHERE product_id = ?",
            (current_quantity + quantity, product_id)
        )
    else:
        conn.execute(
            "INSERT INTO cart (product_id, quantity) VALUES (?, ?)",
            (product_id, quantity)
        )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Product added to cart successfully",
        "product_id": product_id,
        "quantity": current_quantity + quantity
    }), 201


@app.route('/cart', methods=['GET'])
def view_cart():
    """
    View current shopping cart items, line item subtotals,
    applied discount coupon, discount amount, and final total.
    """
    conn = get_db_connection()

    items = conn.execute("""
        SELECT products.id, products.name, products.price,
               cart.quantity,
               ROUND(products.price * cart.quantity, 2) AS subtotal
        FROM cart
        JOIN products ON cart.product_id = products.id
        ORDER BY products.id
    """).fetchall()

    cart_items = [dict(item) for item in items]
    subtotal = round(sum(item['subtotal'] for item in cart_items), 2)

    # Check for an active coupon
    active_coupon_row = conn.execute(
        "SELECT coupon_code FROM cart_coupon WHERE id = 1"
    ).fetchone()

    discount_amount = 0.0
    applied_coupon_code = None

    if active_coupon_row and subtotal > 0:
        coupon = conn.execute(
            "SELECT * FROM coupons WHERE code = ?", (active_coupon_row['coupon_code'],)
        ).fetchone()

        if coupon and coupon['is_active'] and subtotal >= coupon['min_order_value']:
            applied_coupon_code = coupon['code']
            if coupon['discount_type'] == 'percent':
                discount_amount = round(subtotal * (coupon['discount_value'] / 100.0), 2)
            else:  # flat
                discount_amount = min(coupon['discount_value'], subtotal)
        else:
            # Cart value fell below minimum order value; automatically invalidate
            conn.execute("DELETE FROM cart_coupon WHERE id = 1")
            conn.commit()

    conn.close()

    final_total = max(0.0, round(subtotal - discount_amount, 2))

    return jsonify({
        "items": cart_items,
        "item_count": len(cart_items),
        "subtotal": subtotal,
        "applied_coupon": applied_coupon_code,
        "discount_amount": discount_amount,
        "total": final_total
    }), 200


@app.route('/cart/<int:product_id>', methods=['PUT'])
def update_cart(product_id):
    """Update item quantity in cart with positive integer & stock checks."""
    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON payload"}), 400

    if 'quantity' not in data:
        return jsonify({"error": "Quantity is required"}), 400

    quantity = data['quantity']

    if type(quantity) is not int or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    conn = get_db_connection()

    item = conn.execute(
        "SELECT * FROM cart WHERE product_id = ?", (product_id,)
    ).fetchone()

    if item is None:
        conn.close()
        return jsonify({"error": "Cart item not found"}), 404

    product = conn.execute(
        "SELECT stock FROM products WHERE id = ?", (product_id,)
    ).fetchone()

    if quantity > product['stock']:
        conn.close()
        return jsonify({
            "error": "Insufficient stock",
            "available_stock": product['stock'],
            "requested_quantity": quantity
        }), 400

    conn.execute(
        "UPDATE cart SET quantity = ? WHERE product_id = ?",
        (quantity, product_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Cart quantity updated successfully",
        "product_id": product_id,
        "quantity": quantity
    }), 200


@app.route('/cart/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    """Remove a specific item from the shopping cart."""
    conn = get_db_connection()

    item = conn.execute(
        "SELECT * FROM cart WHERE product_id = ?", (product_id,)
    ).fetchone()

    if item is None:
        conn.close()
        return jsonify({"error": "Cart item not found"}), 404

    conn.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Product removed from cart successfully",
        "product_id": product_id
    }), 200


@app.route('/cart', methods=['DELETE'])
def clear_cart():
    """Remove all items and active coupon from the shopping cart."""
    conn = get_db_connection()
    conn.execute("DELETE FROM cart")
    conn.execute("DELETE FROM cart_coupon")
    conn.commit()
    conn.close()

    return jsonify({"message": "Cart cleared successfully"}), 200


# ==========================================================
# 4. DISCOUNT COUPON APIS
# ==========================================================
@app.route('/coupons', methods=['GET'])
def get_coupons():
    """Retrieve all available discount coupons."""
    conn = get_db_connection()
    coupons = conn.execute("SELECT * FROM coupons ORDER BY code").fetchall()
    conn.close()
    return jsonify([dict(c) for c in coupons]), 200


@app.route('/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    """
    Apply a discount coupon to the shopping cart.
    Validates coupon existence, active status, non-empty cart, and minimum order value.
    """
    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict) or 'code' not in data:
        return jsonify({"error": "Coupon code is required"}), 400

    code = str(data['code']).strip().upper()

    conn = get_db_connection()

    coupon = conn.execute(
        "SELECT * FROM coupons WHERE code = ?", (code,)
    ).fetchone()

    if coupon is None:
        conn.close()
        return jsonify({"error": "Coupon code not found"}), 404

    if not coupon['is_active']:
        conn.close()
        return jsonify({"error": "Coupon code is expired or inactive"}), 400

    # Calculate current cart subtotal
    cart_items = conn.execute("""
        SELECT products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
    """).fetchall()

    if not cart_items:
        conn.close()
        return jsonify({"error": "Cannot apply coupon to an empty cart"}), 400

    subtotal = round(sum(item['price'] * item['quantity'] for item in cart_items), 2)

    if subtotal < coupon['min_order_value']:
        conn.close()
        return jsonify({
            "error": f"Minimum order value of {coupon['min_order_value']} required for coupon '{code}'",
            "current_subtotal": subtotal,
            "min_order_value": coupon['min_order_value']
        }), 400

    # Calculate discount amount
    if coupon['discount_type'] == 'percent':
        discount_amount = round(subtotal * (coupon['discount_value'] / 100.0), 2)
    else:  # flat discount
        discount_amount = min(coupon['discount_value'], subtotal)

    final_total = max(0.0, round(subtotal - discount_amount, 2))

    # Save active coupon to cart_coupon table (replaces any previous coupon)
    conn.execute("INSERT OR REPLACE INTO cart_coupon (id, coupon_code) VALUES (1, ?)", (code,))
    conn.commit()
    conn.close()

    return jsonify({
        "message": f"Coupon '{code}' applied successfully",
        "coupon_code": code,
        "discount_type": coupon['discount_type'],
        "discount_value": coupon['discount_value'],
        "discount_amount": discount_amount,
        "subtotal": subtotal,
        "final_total": final_total
    }), 200


@app.route('/cart/coupon', methods=['DELETE'])
def remove_coupon():
    """Remove any applied discount coupon from the shopping cart."""
    conn = get_db_connection()
    conn.execute("DELETE FROM cart_coupon WHERE id = 1")
    conn.commit()
    conn.close()

    return jsonify({"message": "Coupon removed from cart successfully"}), 200


# ==========================================================
# 5. CHECKOUT & ORDER MANAGEMENT APIS
# ==========================================================
@app.route('/cart/checkout', methods=['POST'])
def checkout():
    """
    Checkout current shopping cart:
    1. Validates cart is not empty.
    2. Verifies stock availability for every item.
    3. Calculates subtotal, applies discount if coupon exists, calculates final total.
    4. Records order in 'orders' table.
    5. Records line items in 'order_items' table.
    6. Deducts inventory from 'products' table.
    7. Clears cart and applied coupon.
    """
    conn = get_db_connection()

    cart_items = conn.execute("""
        SELECT cart.product_id, cart.quantity, products.name, products.price, products.stock
        FROM cart
        JOIN products ON cart.product_id = products.id
    """).fetchall()

    if not cart_items:
        conn.close()
        return jsonify({"error": "Cannot checkout an empty cart"}), 400

    # Verify inventory availability
    for item in cart_items:
        if item['quantity'] > item['stock']:
            conn.close()
            return jsonify({
                "error": f"Insufficient stock for product '{item['name']}'",
                "available_stock": item['stock'],
                "requested_quantity": item['quantity']
            }), 400

    subtotal = round(sum(item['price'] * item['quantity'] for item in cart_items), 2)

    # Check for active coupon
    active_coupon_row = conn.execute(
        "SELECT coupon_code FROM cart_coupon WHERE id = 1"
    ).fetchone()

    discount_amount = 0.0
    applied_coupon_code = None

    if active_coupon_row:
        coupon = conn.execute(
            "SELECT * FROM coupons WHERE code = ?", (active_coupon_row['coupon_code'],)
        ).fetchone()

        if coupon and coupon['is_active'] and subtotal >= coupon['min_order_value']:
            applied_coupon_code = coupon['code']
            if coupon['discount_type'] == 'percent':
                discount_amount = round(subtotal * (coupon['discount_value'] / 100.0), 2)
            else:
                discount_amount = min(coupon['discount_value'], subtotal)

    total_amount = max(0.0, round(subtotal - discount_amount, 2))

    # Create Order record
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (subtotal, discount_amount, applied_coupon, total_amount, status)
        VALUES (?, ?, ?, ?, ?)
    """, (subtotal, discount_amount, applied_coupon_code, total_amount, "CONFIRMED"))
    order_id = cursor.lastrowid

    # Record order items and deduct stock
    purchased_items = []
    for item in cart_items:
        item_subtotal = round(item['price'] * item['quantity'], 2)
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, quantity, price, subtotal)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, item['product_id'], item['name'], item['quantity'], item['price'], item_subtotal))

        cursor.execute("""
            UPDATE products SET stock = stock - ? WHERE id = ?
        """, (item['quantity'], item['product_id']))

        purchased_items.append({
            "product_id": item['product_id'],
            "name": item['name'],
            "price": item['price'],
            "quantity": item['quantity'],
            "subtotal": item_subtotal
        })

    # Clear shopping cart and active coupon
    cursor.execute("DELETE FROM cart")
    cursor.execute("DELETE FROM cart_coupon")

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Order placed successfully",
        "order_id": order_id,
        "status": "CONFIRMED",
        "subtotal": subtotal,
        "applied_coupon": applied_coupon_code,
        "discount_amount": discount_amount,
        "total_amount": total_amount,
        "items": purchased_items
    }), 201


@app.route('/orders', methods=['GET'])
def get_orders():
    """Retrieve all confirmed orders."""
    conn = get_db_connection()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(order) for order in orders]), 200


@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Retrieve details and purchased items for a specific order ID."""
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if order is None:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    items = conn.execute(
        "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
    ).fetchall()
    conn.close()

    result = dict(order)
    result['items'] = [dict(item) for item in items]
    return jsonify(result), 200


# ==========================================================
# 6. TEST AUTOMATION STATE RESET API
# ==========================================================
@app.route('/reset', methods=['POST'])
def reset_database():
    """
    Resets the database to a clean, deterministic state.
    Used before automated test suites to ensure repeatable test runs.
    """
    conn = get_db_connection()
    conn.execute("DELETE FROM cart")
    conn.execute("DELETE FROM cart_coupon")
    conn.execute("DELETE FROM order_items")
    conn.execute("DELETE FROM orders")
    conn.execute("DELETE FROM products")
    conn.execute("DELETE FROM coupons")

    # Re-insert standard products
    conn.executemany(
        "INSERT INTO products (id, name, price, stock) VALUES (?, ?, ?, ?)",
        [
            (1, "Laptop", 55000.0, 10),
            (2, "Smartphone", 20000.0, 15),
            (3, "Headphones", 1500.0, 25),
            (4, "Keyboard", 800.0, 20),
            (5, "Mouse", 500.0, 30)
        ]
    )

    # Re-insert standard coupons
    conn.executemany(
        "INSERT INTO coupons (code, discount_type, discount_value, min_order_value, is_active) VALUES (?, ?, ?, ?, ?)",
        [
            ("SAVE10", "percent", 10.0, 1000.0, 1),
            ("FLAT500", "flat", 500.0, 2000.0, 1),
            ("MEGA20", "percent", 20.0, 10000.0, 1),
            ("EXPIRED50", "percent", 50.0, 500.0, 0)
        ]
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Database reset successfully to initial state"
    }), 200


if __name__ == '__main__':
    initialize_database()
    app.run(host='0.0.0.0', port=5000, debug=True)

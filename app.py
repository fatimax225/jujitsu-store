
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
import sqlite3

app = Flask(__name__)
app.secret_key = 'jujita_gifts_secret_2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True

UPLOAD_FOLDER = 'static/images/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ADMIN_USERNAME = 'jojo'
ADMIN_PASSWORD = '2256'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    if os.getenv("RENDER"):  # إذا على Render
        db_path = os.path.join('/data', 'database.db')
    else:  # إذا على جهازك
        db_path = 'database.db'

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        description_ar TEXT,
        image TEXT,
        customizable_options TEXT,
        discount_percent REAL DEFAULT 0,
        stock INTEGER DEFAULT 100,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        customer_address TEXT NOT NULL,
        items TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        payment_proof TEXT,
        payment_confirmed INTEGER DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        rating INTEGER NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        title_ar TEXT,
        description TEXT,
        discount_percent REAL NOT NULL,
        category TEXT,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Seed sample products
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        sample_products = [
            ('Luxury Rose Box', 'صندوق الورد الفاخر', 12.500, 'birthday', 'Beautiful handcrafted rose arrangement in an elegant gift box', 'ترتيب ورد مصنوع يدويًا في صندوق هدايا أنيق', 'default_roses.jpg', json.dumps(['Red', 'Pink', 'White', 'Mixed']), 0),
            ('Eid Gift Basket', 'سلة هدايا العيد', 18.000, 'eid', 'Premium Eid gift basket with assorted sweets and chocolates', 'سلة هدايا العيد المميزة مع حلويات وشوكولاتة متنوعة', 'default_eid.jpg', json.dumps(['Small', 'Medium', 'Large']), 10),
            ('Chocolate Bouquet', 'باقة الشوكولاتة', 8.500, 'birthday', 'Elegant bouquet made entirely of premium chocolates', 'باقة أنيقة مصنوعة بالكامل من الشوكولاتة الفاخرة', 'default_choc.jpg', json.dumps(['Milk Chocolate', 'Dark Chocolate', 'White Chocolate', 'Mixed']), 0),
            ('Ramadan Lantern Set', 'طقم فوانيس رمضان', 22.000, 'ramadan', 'Traditional Ramadan lanterns with premium dates and Arabic coffee', 'فوانيس رمضان التقليدية مع تمر فاخر وقهوة عربية', 'default_ramadan.jpg', json.dumps(['Gold', 'Silver', 'Rose Gold']), 15),
            ('Spa Relaxation Kit', 'طقم الاسترخاء', 25.000, 'special', 'Complete spa kit with bath salts, candles, and luxury soaps', 'طقم سبا كامل مع أملاح الحمام والشموع والصابون الفاخر', 'default_spa.jpg', json.dumps(['Lavender', 'Rose', 'Vanilla', 'Ocean']), 0),
            ('Baby Shower Gift', 'هدية استقبال المولود', 30.000, 'baby', 'Adorable baby gift set with plush toys and baby essentials', 'طقم هدايا الأطفال الرائع مع دمى وضروريات الأطفال', 'default_baby.jpg', json.dumps(['Blue', 'Pink', 'Neutral']), 5),
        ]
        c.executemany('''INSERT INTO products (name, name_ar, price, category, description, description_ar, image, customizable_options, discount_percent) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', sample_products)

    conn.commit()
    conn.close()

# ─── Context Processor ───────────────────────────────────────────────
@app.context_processor
def inject_cart_count():
    cart = session.get('cart', {})
    count = sum(item.get('quantity', 1) for item in cart.values())
    lang = session.get('lang', 'en')
    return dict(cart_count=count, lang=lang)

# ─── Language Switch ──────────────────────────────────────────────────
@app.route('/set_lang/<lang>')
def set_lang(lang):
    session['lang'] = lang if lang in ['en', 'ar'] else 'en'
    return redirect(request.referrer or url_for('index'))

# ─── Main Routes ──────────────────────────────────────────────────────
@app.route('/')
def index():
    conn = get_db()
    featured = conn.execute('SELECT * FROM products ORDER BY RANDOM() LIMIT 6').fetchall()
    categories = conn.execute('SELECT DISTINCT category FROM products').fetchall()
    offers = conn.execute('SELECT * FROM offers WHERE active=1').fetchall()
    conn.close()
    return render_template('index.html', featured=featured, categories=categories, offers=offers)

@app.route('/products')
def products():
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    conn = get_db()
    query = 'SELECT * FROM products WHERE 1=1'
    params = []
    if category:
        query += ' AND category = ?'
        params.append(category)
    if search:
        query += ' AND (name LIKE ? OR name_ar LIKE ? OR description LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    query += ' ORDER BY created_at DESC'
    prods = conn.execute(query, params).fetchall()
    categories = conn.execute('SELECT DISTINCT category FROM products').fetchall()
    conn.close()
    return render_template('products.html', products=prods, categories=categories,
                           selected_category=category, search=search)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db()
    product = conn.execute('SELECT * FROM products WHERE id = %s', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('products'))
    reviews = conn.execute('''SELECT r.*, u.name as reviewer_name FROM reviews r 
                              JOIN users u ON r.user_id = u.id 
                              WHERE r.product_id = %s ORDER BY r.created_at DESC''', (product_id,)).fetchall()
    avg_rating = conn.execute('SELECT AVG(rating) FROM reviews WHERE product_id = %s', (product_id,)).fetchone()[0]
    related = conn.execute('SELECT * FROM products WHERE category = %s AND id != %s LIMIT 4',
                           (product['category'], product_id)).fetchall()
    conn.close()
    options = json.loads(product['customizable_options']) if product['customizable_options'] else []
    return render_template('product_detail.html', product=product, reviews=reviews,
                           avg_rating=avg_rating, related=related, options=options)

# ─── Auth Routes ──────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        if not all([name, email, password]):
            flash('Please fill all required fields', 'error')
            return render_template('register.html')
        conn = get_db()
        existing = conn.execute('SELECT id FROM users WHERE email = %s', (email,)).fetchone()
        if existing:
            flash('Email already registered', 'error')
            conn.close()
            return render_template('register.html')
        hashed = generate_password_hash(password)
        conn.execute('INSERT INTO users (name, email, password, phone, address) VALUES (?, ?, ?, ?, ?)',
                     (name, email, hashed, phone, address))
        conn.commit()
        conn.close()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = %s', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# ─── Cart Routes ──────────────────────────────────────────────────────
@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    if cart:
        conn = get_db()
        product_ids = list(cart.keys())
        placeholders = ','.join(['?' for _ in product_ids])
        products_list = conn.execute(f'SELECT * FROM products WHERE id IN ({placeholders})', product_ids).fetchall()
        conn.close()
    else:
        products_list = []
    total = 0
    cart_items = []
    for product in products_list:
        pid = str(product['id'])
        qty = cart[pid]['quantity']
        price = product['price'] * (1 - product['discount_percent'] / 100)
        subtotal = price * qty
        total += subtotal
        cart_items.append({'product': product, 'quantity': qty,
                           'option': cart[pid].get('option', ''), 'subtotal': subtotal, 'price': price})
    return render_template('cart.html', cart_items=cart_items, total=total+1)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    product_id = str(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))
    option = request.form.get('option', '')
    cart = session.get('cart', {})
    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {'quantity': quantity, 'option': option}
    session['cart'] = cart
    flash('Item added to cart!', 'success')
    return redirect(request.referrer or url_for('products'))

@app.route('/cart/update', methods=['POST'])
def update_cart():
    product_id = str(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    if product_id in cart:
        if quantity <= 0:
            del cart[product_id]
        else:
            cart[product_id]['quantity'] = quantity
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart/remove/<product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))

# ─── Checkout & Orders ────────────────────────────────────────────────
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        notes = request.form.get('notes', '')
        if not all([name, phone, address]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('checkout'))
        conn = get_db()
        product_ids = list(cart.keys())
        placeholders = ','.join(['?' for _ in product_ids])
        products_list = conn.execute(f'SELECT * FROM products WHERE id IN ({placeholders})', product_ids).fetchall()
        total = 0
        items = []
        for product in products_list:
            pid = str(product['id'])
            qty = cart[pid]['quantity']
            price = product['price'] * (1 - product['discount_percent'] / 100)
            subtotal = price * qty
            total += subtotal
            items.append({'id': product['id'], 'name': product['name'],
                          'price': price, 'quantity': qty, 'option': cart[pid].get('option', ''),
                          'subtotal': subtotal})
        order_number = 'JG-' + str(uuid.uuid4())[:8].upper()
        user_id = session.get('user_id')
        conn.execute('''INSERT INTO orders (order_number, user_id, customer_name, customer_phone, 
                        customer_address, items, total_amount, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (order_number, user_id, name, phone, address, json.dumps(items), total, notes))
        conn.commit()
        conn.close()
        session['cart'] = {}
        session['last_order'] = {'order_number': order_number, 'total': total,
                                 'name': name, 'items': items}
        return redirect(url_for('order_confirmation'))
    # Pre-fill if logged in
    user_data = {}
    if session.get('user_id'):
        conn = get_db()
        user_data = conn.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],)).fetchone()
        conn.close()
    # Calculate totals
    conn = get_db()
    product_ids = list(cart.keys())
    placeholders = ','.join(['?' for _ in product_ids])
    products_list = conn.execute(f'SELECT * FROM products WHERE id IN ({placeholders})', product_ids).fetchall()
    conn.close()
    total = 0
    cart_items = []
    for product in products_list:
        pid = str(product['id'])
        qty = cart[pid]['quantity']
        price = product['price'] * (1 - product['discount_percent'] / 100)
        subtotal = price * qty
        total += subtotal
        cart_items.append({'product': product, 'quantity': qty, 'subtotal': subtotal, 'price': price})
    return render_template('checkout.html', cart_items=cart_items, total=total, user_data=user_data)

@app.route('/order/confirmation')
def order_confirmation():
    order = session.get('last_order')
    if not order:
        return redirect(url_for('index'))
    return render_template('order_confirmation.html', order=order)

@app.route('/order/upload_proof', methods=['POST'])
def upload_proof():
    order_number = request.form.get('order_number')
    if 'proof' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('order_confirmation'))
    file = request.files['proof']
    if file and allowed_file(file.filename):
        filename = secure_filename(f"proof_{order_number}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        conn = get_db()
        conn.execute('UPDATE orders SET payment_proof = ?, status = ? WHERE order_number = %s',
                     (filename, 'payment_uploaded', order_number))
        conn.commit()
        conn.close()
        flash('Payment proof uploaded successfully!', 'success')
    return redirect(url_for('index'))

# ─── Reviews ─────────────────────────────────────────────────────────
@app.route('/review/add', methods=['POST'])
def add_review():
    if not session.get('user_id'):
        flash('Please login to write a review', 'error')
        return redirect(url_for('login'))
    product_id = request.form.get('product_id')
    rating = request.form.get('rating')
    comment = request.form.get('comment', '')
    conn = get_db()
    existing = conn.execute('SELECT id FROM reviews WHERE product_id = ? AND user_id = ?',
                            (product_id, session['user_id'])).fetchone()
    if existing:
        flash('You have already reviewed this product', 'error')
    else:
        conn.execute('INSERT INTO reviews (product_id, user_id, user_name, rating, comment) VALUES (?, ?, ?, ?, ?)',
                     (product_id, session['user_id'], session['user_name'], rating, comment))
        conn.commit()
        flash('Review submitted!', 'success')
    conn.close()
    return redirect(url_for('product_detail', product_id=product_id))

# ─── Static Pages ─────────────────────────────────────────────────────
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ─── Admin Routes ─────────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            session.permanent = False
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()
    total_products = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    total_orders = conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    total_revenue = conn.execute('SELECT SUM(total_amount) FROM orders WHERE status != "cancelled"').fetchone()[0] or 0
    recent_orders = conn.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('admin/dashboard.html', total_products=total_products,
                           total_orders=total_orders, total_users=total_users,
                           total_revenue=total_revenue, recent_orders=recent_orders)

@app.route('/admin/products')
@admin_required
def admin_products():
    conn = get_db()
    products = conn.execute('SELECT * FROM products ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        name_ar = request.form.get('name_ar', '')
        price = float(request.form.get('price', 0))
        category = request.form.get('category')
        description = request.form.get('description', '')
        description_ar = request.form.get('description_ar', '')
        discount = float(request.form.get('discount_percent', 0))
        stock = int(request.form.get('stock', 100))
        options_raw = request.form.get('customizable_options', '')
        options = json.dumps([o.strip() for o in options_raw.split(',') if o.strip()])
        image_filename = 'default_product.jpg'
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename
        conn = get_db()
        conn.execute('''INSERT INTO products (name, name_ar, price, category, description, description_ar, 
                        image, customizable_options, discount_percent, stock) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (name, name_ar, price, category, description, description_ar,
                      image_filename, options, discount, stock))
        conn.commit()
        conn.close()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', product=None, action='add')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    conn = get_db()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('admin_products'))
    if request.method == 'POST':
        name = request.form.get('name')
        name_ar = request.form.get('name_ar', '')
        price = float(request.form.get('price', 0))
        category = request.form.get('category')
        description = request.form.get('description', '')
        description_ar = request.form.get('description_ar', '')
        discount = float(request.form.get('discount_percent', 0))
        stock = int(request.form.get('stock', 100))
        options_raw = request.form.get('customizable_options', '')
        options = json.dumps([o.strip() for o in options_raw.split(',') if o.strip()])
        image_filename = product['image']
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename
        conn.execute('''UPDATE products SET name=?, name_ar=?, price=?, category=?, description=?, 
                        description_ar=?, image=?, customizable_options=?, discount_percent=?, stock=? 
                        WHERE id=?''',
                     (name, name_ar, price, category, description, description_ar,
                      image_filename, options, discount, stock, product_id))
        conn.commit()
        flash('Product updated!', 'success')
        conn.close()
        return redirect(url_for('admin_products'))
    conn.close()
    options = json.loads(product['customizable_options']) if product['customizable_options'] else []
    return render_template('admin/product_form.html', product=product,
                           options=', '.join(options), action='edit')

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    conn = get_db()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    flash('Product deleted', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    conn = get_db()
    orders = conn.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    conn = get_db()
    order = conn.execute('SELECT * FROM orders WHERE id = %s', (order_id,)).fetchone()
    conn.close()
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('admin_orders'))
    items = json.loads(order['items'])
    return render_template('admin/order_detail.html', order=order, items=items)

@app.route('/admin/orders/update_status/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    status = request.form.get('status')
    conn = get_db()
    conn.execute('UPDATE orders SET status = ? WHERE id = %s', (status, order_id))
    conn.commit()
    conn.close()
    flash('Order status updated', 'success')
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/users.html', users=users)

@app.route('/admin/offers')
@admin_required
def admin_offers():
    conn = get_db()
    offers = conn.execute('SELECT * FROM offers ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/offers.html', offers=offers)

@app.route('/admin/offers/add', methods=['POST'])
@admin_required
def admin_add_offer():
    title = request.form.get('title')
    title_ar = request.form.get('title_ar', '')
    description = request.form.get('description', '')
    discount = float(request.form.get('discount_percent', 0))
    category = request.form.get('category', '')
    conn = get_db()
    conn.execute('INSERT INTO offers (title, title_ar, description, discount_percent, category) VALUES (?, ?, ?, ?, ?)',
                 (title, title_ar, description, discount, category))
    conn.commit()
    conn.close()
    flash('Offer added!', 'success')
    return redirect(url_for('admin_offers'))

@app.route('/admin/offers/toggle/<int:offer_id>')
@admin_required
def admin_toggle_offer(offer_id):
    conn = get_db()
    offer = conn.execute('SELECT active FROM offers WHERE id = %s', (offer_id,)).fetchone()
    new_status = 0 if offer['active'] else 1
    conn.execute('UPDATE offers SET active = ? WHERE id = %s', (new_status, offer_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_offers'))

@app.route('/admin/offers/delete/<int:offer_id>', methods=['POST'])
@admin_required
def admin_delete_offer(offer_id):
    conn = get_db()
    conn.execute('DELETE FROM offers WHERE id = %s', (offer_id,))
    conn.commit()
    conn.close()
    flash('Offer deleted', 'success')
    return redirect(url_for('admin_offers'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    app.run(debug=True, use_reloader=True, port=5002)

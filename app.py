import os
import json
import uuid
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()

# ── Cloudinary ────────────────────────────────────────────────────────
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dn5verarm'),
    api_key    = os.environ.get('CLOUDINARY_API_KEY',    '516669919435842'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET', 'LkrWtnrFm_YgX7iUooCCqC'),
    secure     = True
)

def upload_to_cloudinary(file_obj, folder='jujita'):
    try:
        result = cloudinary.uploader.upload(
            file_obj, folder=folder, resource_type='image',
            allowed_formats=['jpg','jpeg','png','gif','webp'],
        )
        return result.get('secure_url')
    except Exception as e:
        print(f"[Cloudinary] Upload failed: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════
#  App & Config
# ══════════════════════════════════════════════════════════════════════
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.environ.get('SECRET_KEY', 'jujita_gifts_secret_2024')

_db_url = os.environ.get('DATABASE_URL') or 'sqlite:///jujita_local.db'
app.config['SQLALCHEMY_DATABASE_URI']      = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS']    = {'pool_pre_ping': True, 'pool_recycle': 300}

UPLOAD_FOLDER      = 'static/images/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'jojo')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '2256')

db      = SQLAlchemy(app)
migrate = Migrate(app, db)


# ══════════════════════════════════════════════════════════════════════
#  Models
# ══════════════════════════════════════════════════════════════════════
class User(db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(200), unique=True, nullable=False)
    password   = db.Column(db.Text, nullable=False)
    phone      = db.Column(db.String(30))
    address    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders  = db.relationship('Order',  backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)


class Product(db.Model):
    __tablename__ = 'products'
    id                   = db.Column(db.Integer, primary_key=True)
    name                 = db.Column(db.String(200), nullable=False)
    name_ar              = db.Column(db.String(200))
    price                = db.Column(db.Float, nullable=False)
    category             = db.Column(db.String(80), nullable=False)
    description          = db.Column(db.Text)
    description_ar       = db.Column(db.Text)
    image                = db.Column(db.String(500), default='default_product.jpg')
    customizable_options = db.Column(db.Text)
    discount_percent     = db.Column(db.Float, default=0)
    stock                = db.Column(db.Integer, default=100)
    is_hidden            = db.Column(db.Boolean, default=False)
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan')
    images  = db.relationship('ProductImage', backref='product', lazy=True,
                              cascade='all, delete-orphan', order_by='ProductImage.sort_order')

    @property
    def options_list(self):
        try:    return json.loads(self.customizable_options) if self.customizable_options else []
        except: return []

    @property
    def final_price(self):
        return self.price * (1 - self.discount_percent / 100)


class Order(db.Model):
    __tablename__ = 'orders'
    id                = db.Column(db.Integer, primary_key=True)
    order_number      = db.Column(db.String(30), unique=True, nullable=False)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_name     = db.Column(db.String(150), nullable=False)
    customer_phone    = db.Column(db.String(30), nullable=False)
    customer_address  = db.Column(db.Text, nullable=False)
    items             = db.Column(db.Text, nullable=False)
    total_amount      = db.Column(db.Float, nullable=False)
    status            = db.Column(db.String(40), default='pending')
    payment_proof     = db.Column(db.String(500))
    payment_confirmed = db.Column(db.Boolean, default=False)
    notes             = db.Column(db.Text)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def items_list(self):
        try:    return json.loads(self.items)
        except: return []


class Review(db.Model):
    __tablename__ = 'reviews'
    id         = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_name  = db.Column(db.String(120), nullable=False)
    rating     = db.Column(db.Integer, nullable=False)
    comment    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Offer(db.Model):
    __tablename__ = 'offers'
    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(200), nullable=False)
    title_ar         = db.Column(db.String(200))
    description      = db.Column(db.Text)
    discount_percent = db.Column(db.Float, nullable=False)
    category         = db.Column(db.String(80))
    active           = db.Column(db.Boolean, default=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)


class ProductImage(db.Model):
    __tablename__ = 'product_images'
    id         = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    url        = db.Column(db.String(500), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PhotoOrder(db.Model):
    __tablename__ = 'photo_orders'
    id             = db.Column(db.Integer, primary_key=True)
    order_ref      = db.Column(db.String(30), unique=True, nullable=False)
    product_id     = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    customer_name  = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=False)
    notes          = db.Column(db.Text)
    qty_label      = db.Column(db.String(50))
    qty_num        = db.Column(db.Integer, default=0)
    price_bd       = db.Column(db.Float, default=0)
    images_json    = db.Column(db.Text)
    upload_later   = db.Column(db.Boolean, default=False)
    status         = db.Column(db.String(40), default='pending')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def images_list(self):
        try:    return json.loads(self.images_json) if self.images_json else []
        except: return []


# ══════════════════════════════════════════════════════════════════════
#  Seed Data
# ══════════════════════════════════════════════════════════════════════
def seed_products():
    if Product.query.count() > 0:
        return
    samples = [
        Product(name='Luxury Rose Box', name_ar='صندوق الورد الفاخر',
                price=12.500, category='birthday',
                description='Beautiful handcrafted rose arrangement',
                description_ar='ترتيب ورد مصنوع يدويًا في صندوق هدايا أنيق',
                image='default_product.jpg',
                customizable_options=json.dumps(['Red', 'Pink', 'White', 'Mixed'])),
        Product(name='Eid Gift Basket', name_ar='سلة هدايا العيد',
                price=18.000, category='eid',
                description='Premium Eid gift basket with assorted sweets',
                description_ar='سلة هدايا العيد المميزة مع حلويات متنوعة',
                image='default_product.jpg',
                customizable_options=json.dumps(['Small', 'Medium', 'Large']),
                discount_percent=10),
    ]
    db.session.add_all(samples)
    db.session.commit()


# ══════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def get_image_url(product):
    """Return best display URL for a product."""
    if hasattr(product, 'images') and product.images:
        return product.images[0].url
    img = product.image if product else None
    if not img or img.startswith('default'):
        return None
    if img.startswith('http'):
        return img
    return url_for('static', filename='images/uploads/' + img)

@app.context_processor
def inject_globals():
    cart  = session.get('cart', {})
    count = sum(item.get('quantity', 1) for item in cart.values())
    lang  = session.get('lang', 'en')
    return dict(cart_count=count, lang=lang, image_url=get_image_url)

def _build_cart(cart_session):
    if not cart_session:
        return [], 0.0
    ids   = list(cart_session.keys())
    prods = Product.query.filter(Product.id.in_(ids)).all()
    items, total = [], 0.0
    for p in prods:
        pid      = str(p.id)
        qty      = cart_session[pid]['quantity']
        price    = p.final_price
        subtotal = price * qty
        total   += subtotal
        items.append({'product': p, 'quantity': qty,
                      'option': cart_session[pid].get('option', ''),
                      'subtotal': subtotal, 'price': price})
    return items, total


# ══════════════════════════════════════════════════════════════════════
#  Language
# ══════════════════════════════════════════════════════════════════════
@app.route('/set_lang/<lang>')
def set_lang(lang):
    session['lang'] = lang if lang in ['en', 'ar'] else 'en'
    return redirect(request.referrer or url_for('index'))


# ══════════════════════════════════════════════════════════════════════
#  Main Routes
# ══════════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    import sqlalchemy
    featured   = Product.query.filter_by(is_hidden=False).order_by(sqlalchemy.func.random()).limit(6).all()
    categories = db.session.query(Product.category).distinct().all()
    offers     = Offer.query.filter_by(active=True).all()
    return render_template('index.html', featured=featured, categories=categories, offers=offers)


@app.route('/products')
def products():
    category = request.args.get('category', '')
    search   = request.args.get('search', '')
    q = Product.query.filter_by(is_hidden=False)
    if category:
        q = q.filter_by(category=category)
    if search:
        like = f'%{search}%'
        q = q.filter(Product.name.ilike(like) | Product.name_ar.ilike(like) | Product.description.ilike(like))
    prods      = q.order_by(Product.created_at.desc()).all()
    categories = db.session.query(Product.category).distinct().all()
    return render_template('products.html', products=prods, categories=categories,
                           selected_category=category, search=search)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    avg_rating = db.session.query(db.func.avg(Review.rating)).filter_by(product_id=product_id).scalar()
    related = Product.query.filter(Product.category == product.category, Product.id != product_id,
                                   Product.is_hidden == False).limit(4).all()
    product_images = ProductImage.query.filter_by(product_id=product_id).order_by(ProductImage.sort_order).all()
    return render_template('product_detail.html', product=product, reviews=reviews,
                           avg_rating=avg_rating, related=related,
                           options=product.options_list, product_images=product_images)


# ══════════════════════════════════════════════════════════════════════
#  Photo Orders (Magnets / Photo Print)
# ══════════════════════════════════════════════════════════════════════
@app.route('/photo-order/<int:product_id>', methods=['POST'])
def photo_order(product_id):
    product     = Product.query.get_or_404(product_id)
    name        = request.form.get('name', '').strip()
    phone       = request.form.get('phone', '').strip()
    notes       = request.form.get('notes', '')
    qty_label   = request.form.get('qty_label', '')
    upload_later= request.form.get('upload_later') == '1'

    if not name or not phone:
        flash('Please enter your name and phone number.', 'error')
        return redirect(url_for('product_detail', product_id=product_id))

    qty_num = 0
    try: qty_num = int(''.join(c for c in qty_label if c.isdigit()))
    except: pass

    price = product.final_price

    uploaded_urls = []
    if not upload_later:
        files = request.files.getlist('photos')
        for f in files:
            if f and f.filename and allowed_file(f.filename):
                url = upload_to_cloudinary(f, folder='jujita/photo_orders')
                if url:
                    uploaded_urls.append(url)

    order = PhotoOrder(
        order_ref      = 'PH-' + str(uuid.uuid4())[:8].upper(),
        product_id     = product_id,
        customer_name  = name,
        customer_phone = phone,
        notes          = notes,
        qty_label      = qty_label,
        qty_num        = qty_num,
        price_bd       = price,
        images_json    = json.dumps(uploaded_urls),
        upload_later   = upload_later,
    )
    db.session.add(order)
    db.session.commit()

    flash(f'✅ Order received! We will contact you on {phone}.', 'success')
    return redirect(url_for('photo_order_confirm', ref=order.order_ref))


@app.route('/photo-order/confirm/<ref>')
def photo_order_confirm(ref):
    order = PhotoOrder.query.filter_by(order_ref=ref).first_or_404()
    return render_template('photo_order_confirm.html', order=order)


# ══════════════════════════════════════════════════════════════════════
#  Auth Routes
# ══════════════════════════════════════════════════════════════════════
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone    = request.form.get('phone', '').strip()
        address  = request.form.get('address', '').strip()
        if not all([name, email, password]):
            flash('Please fill all required fields', 'error')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        user = User(name=name, email=email, password=generate_password_hash(password),
                    phone=phone, address=address)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id']   = user.id
            session['user_name'] = user.name
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


# ══════════════════════════════════════════════════════════════════════
#  Cart Routes
# ══════════════════════════════════════════════════════════════════════
@app.route('/cart')
def cart():
    cart_items, total = _build_cart(session.get('cart', {}))
    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    pid    = str(request.form.get('product_id'))
    qty    = int(request.form.get('quantity', 1))
    option = request.form.get('option', '')
    cart   = session.get('cart', {})

    product = Product.query.get(int(pid))
    if not product:
        flash('Product not found.', 'error')
        return redirect(request.referrer or url_for('products'))

    if product.stock <= 0:
        flash(f'Sorry, "{product.name}" is out of stock.', 'error')
        return redirect(request.referrer or url_for('products'))

    in_cart = cart.get(pid, {}).get('quantity', 0)
    if in_cart + qty > product.stock:
        avail = product.stock - in_cart
        if avail <= 0:
            flash(f'You already have the max available ({product.stock}) in your cart.', 'error')
            session['cart'] = cart
            return redirect(request.referrer or url_for('products'))
        qty = avail
        flash(f'Only {avail} more available. Added {avail} to cart.', 'error')

    if pid in cart:
        cart[pid]['quantity'] += qty
    else:
        cart[pid] = {'quantity': qty, 'option': option}
    session['cart'] = cart
    flash('Item added to cart!', 'success')
    return redirect(request.referrer or url_for('products'))


@app.route('/cart/update', methods=['POST'])
def update_cart():
    pid  = str(request.form.get('product_id'))
    qty  = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    if pid in cart:
        if qty <= 0:
            del cart[pid]
        else:
            product = Product.query.get(int(pid))
            if product and qty > product.stock:
                qty = product.stock
                flash(f'Capped at available stock ({product.stock}).', 'error')
            cart[pid]['quantity'] = qty
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/cart/remove/<product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))


# ══════════════════════════════════════════════════════════════════════
#  Checkout & Orders
# ══════════════════════════════════════════════════════════════════════
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_session = session.get('cart', {})
    if not cart_session:
        return redirect(url_for('cart'))

    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        phone   = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        notes   = request.form.get('notes', '')
        if not all([name, phone, address]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('checkout'))

        cart_items, total = _build_cart(cart_session)
        items_data = [
            {'id': ci['product'].id, 'name': ci['product'].name,
             'price': ci['price'], 'quantity': ci['quantity'],
             'option': ci['option'], 'subtotal': ci['subtotal']}
            for ci in cart_items
        ]
        order = Order(
            order_number     = 'JG-' + str(uuid.uuid4())[:8].upper(),
            user_id          = session.get('user_id'),
            customer_name    = name, customer_phone = phone,
            customer_address = address, items = json.dumps(items_data),
            total_amount     = total, notes = notes,
        )
        db.session.add(order)
        for ci in cart_items:
            ci['product'].stock = max(0, ci['product'].stock - ci['quantity'])
        db.session.commit()

        session['cart'] = {}
        session['last_order'] = {'order_number': order.order_number,
                                  'total': total, 'name': name,
                                  'phone': phone, 'items': items_data}
        return redirect(url_for('order_confirmation'))

    user_data = None
    if session.get('user_id'):
        user_data = User.query.get(session['user_id'])
    cart_items, total = _build_cart(cart_session)
    return render_template('checkout.html', cart_items=cart_items, total=total, user_data=user_data)


@app.route('/order/confirmation')
def order_confirmation():
    order = session.get('last_order')
    if not order:
        return redirect(url_for('index'))
    if isinstance(order.get('items'), str):
        order['items'] = json.loads(order['items'])
    return render_template('order_confirmation.html', order=order)


@app.route('/order/upload_proof', methods=['POST'])
def upload_proof():
    order_number = request.form.get('order_number')
    if 'proof' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('order_confirmation'))
    file = request.files['proof']
    if file and allowed_file(file.filename):
        url = upload_to_cloudinary(file, folder='jujita/proofs')
        if url:
            order = Order.query.filter_by(order_number=order_number).first()
            if order:
                order.payment_proof = url
                order.status        = 'payment_uploaded'
                db.session.commit()
            flash('Payment proof uploaded successfully!', 'success')
        else:
            flash('Upload failed. Please try again.', 'error')
    return redirect(url_for('index'))


# ══════════════════════════════════════════════════════════════════════
#  Reviews
# ══════════════════════════════════════════════════════════════════════
@app.route('/review/add', methods=['POST'])
def add_review():
    if not session.get('user_id'):
        flash('Please login to write a review', 'error')
        return redirect(url_for('login'))
    pid      = request.form.get('product_id')
    existing = Review.query.filter_by(product_id=pid, user_id=session['user_id']).first()
    if existing:
        flash('You have already reviewed this product', 'error')
    else:
        review = Review(product_id=pid, user_id=session['user_id'],
                        user_name=session['user_name'],
                        rating=int(request.form.get('rating', 5)),
                        comment=request.form.get('comment', ''))
        db.session.add(review)
        db.session.commit()
        flash('Review submitted!', 'success')
    return redirect(url_for('product_detail', product_id=pid))


# ══════════════════════════════════════════════════════════════════════
#  Static Pages
# ══════════════════════════════════════════════════════════════════════
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/scoop')
def scoop():
    return render_template('scoop.html')


# ══════════════════════════════════════════════════════════════════════
#  Admin — Login / Logout
# ══════════════════════════════════════════════════════════════════════
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


# ══════════════════════════════════════════════════════════════════════
#  Admin — Dashboard
# ══════════════════════════════════════════════════════════════════════
@app.route('/admin')
@admin_required
def admin_dashboard():
    total_products = Product.query.count()
    total_orders   = Order.query.count()
    total_users    = User.query.count()
    total_revenue  = db.session.query(db.func.sum(Order.total_amount)).filter(Order.status != 'cancelled').scalar() or 0
    recent_orders  = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', total_products=total_products,
                           total_orders=total_orders, total_users=total_users,
                           total_revenue=total_revenue, recent_orders=recent_orders)


# ══════════════════════════════════════════════════════════════════════
#  Admin — Products
# ══════════════════════════════════════════════════════════════════════
@app.route('/admin/products')
@admin_required
def admin_products():
    filter_by = request.args.get('filter', '')
    if filter_by == 'hidden':
        prods = Product.query.filter_by(is_hidden=True).order_by(Product.created_at.desc()).all()
    else:
        prods = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=prods)


@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        # Handle multiple images
        files = request.files.getlist('images')
        image_filename = 'default_product.jpg'
        gallery_urls   = []
        for i, file in enumerate(files):
            if file and file.filename and allowed_file(file.filename):
                url = upload_to_cloudinary(file)
                if url:
                    if i == 0:
                        image_filename = url
                    else:
                        gallery_urls.append(url)

        options_raw = request.form.get('customizable_options', '')
        options     = json.dumps([o.strip() for o in options_raw.split(',') if o.strip()])

        product = Product(
            name=request.form.get('name'), name_ar=request.form.get('name_ar', ''),
            price=float(request.form.get('price', 0)),
            category=request.form.get('category'),
            description=request.form.get('description', ''),
            description_ar=request.form.get('description_ar', ''),
            image=image_filename, customizable_options=options,
            discount_percent=float(request.form.get('discount_percent', 0)),
            stock=int(request.form.get('stock', 100)),
        )
        db.session.add(product)
        db.session.flush()
        for order_i, u in enumerate(gallery_urls, 1):
            db.session.add(ProductImage(product_id=product.id, url=u, sort_order=order_i))
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', product=None, options='', action='add')


@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        files = request.files.getlist('images')
        valid = [f for f in files if f and f.filename and allowed_file(f.filename)]
        if valid:
            url = upload_to_cloudinary(valid[0])
            if url:
                product.image = url
            max_o = db.session.query(db.func.max(ProductImage.sort_order)).filter_by(product_id=product.id).scalar() or 0
            for i, f in enumerate(valid[1:], 1):
                u = upload_to_cloudinary(f)
                if u:
                    db.session.add(ProductImage(product_id=product.id, url=u, sort_order=max_o + i))

        options_raw              = request.form.get('customizable_options', '')
        product.name             = request.form.get('name')
        product.name_ar          = request.form.get('name_ar', '')
        product.price            = float(request.form.get('price', 0))
        product.category         = request.form.get('category')
        product.description      = request.form.get('description', '')
        product.description_ar   = request.form.get('description_ar', '')
        product.customizable_options = json.dumps([o.strip() for o in options_raw.split(',') if o.strip()])
        product.discount_percent = float(request.form.get('discount_percent', 0))
        product.stock            = int(request.form.get('stock', 100))
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', product=product,
                           options=', '.join(product.options_list), action='edit')


@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/products/toggle_hide/<int:product_id>', methods=['POST'])
@admin_required
def admin_toggle_hide(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_hidden = not product.is_hidden
    db.session.commit()
    flash(f'"{product.name}" is now {"Hidden" if product.is_hidden else "Visible"}', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/products/images/delete/<int:image_id>', methods=['POST'])
@admin_required
def admin_delete_product_image(image_id):
    img = ProductImage.query.get_or_404(image_id)
    product_id = img.product_id
    db.session.delete(img)
    db.session.commit()
    flash('Image deleted.', 'success')
    return redirect(url_for('admin_edit_product', product_id=product_id))


# ══════════════════════════════════════════════════════════════════════
#  Admin — Orders
# ══════════════════════════════════════════════════════════════════════
@app.route('/admin/orders')
@admin_required
def admin_orders():
    status = request.args.get('status', '')
    q = Order.query
    if status:
        q = q.filter_by(status=status)
    orders = q.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order, items=order.items_list)


@app.route('/admin/orders/update_status/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    order        = Order.query.get_or_404(order_id)
    order.status = request.form.get('status')
    db.session.commit()
    flash('Order status updated', 'success')
    return redirect(url_for('admin_order_detail', order_id=order_id))


# ══════════════════════════════════════════════════════════════════════
#  Admin — Photo Orders
# ══════════════════════════════════════════════════════════════════════
@app.route('/admin/photo-orders')
@admin_required
def admin_photo_orders():
    orders = PhotoOrder.query.order_by(PhotoOrder.created_at.desc()).all()
    return render_template('admin/photo_orders.html', orders=orders)


@app.route('/admin/photo-orders/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_photo_order_status(order_id):
    order        = PhotoOrder.query.get_or_404(order_id)
    order.status = request.form.get('status', 'pending')
    db.session.commit()
    flash('Status updated!', 'success')
    return redirect(url_for('admin_photo_orders'))


# ══════════════════════════════════════════════════════════════════════
#  Admin — Users
# ══════════════════════════════════════════════════════════════════════
@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


# ══════════════════════════════════════════════════════════════════════
#  Admin — Offers
# ══════════════════════════════════════════════════════════════════════
@app.route('/admin/offers')
@admin_required
def admin_offers():
    offers = Offer.query.order_by(Offer.created_at.desc()).all()
    return render_template('admin/offers.html', offers=offers)


@app.route('/admin/offers/add', methods=['POST'])
@admin_required
def admin_add_offer():
    offer = Offer(title=request.form.get('title'), title_ar=request.form.get('title_ar', ''),
                  description=request.form.get('description', ''),
                  discount_percent=float(request.form.get('discount_percent', 0)),
                  category=request.form.get('category', ''))
    db.session.add(offer)
    db.session.commit()
    flash('Offer added!', 'success')
    return redirect(url_for('admin_offers'))


@app.route('/admin/offers/toggle/<int:offer_id>')
@admin_required
def admin_toggle_offer(offer_id):
    offer        = Offer.query.get_or_404(offer_id)
    offer.active = not offer.active
    db.session.commit()
    return redirect(url_for('admin_offers'))


@app.route('/admin/offers/delete/<int:offer_id>', methods=['POST'])
@admin_required
def admin_delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    flash('Offer deleted', 'success')
    return redirect(url_for('admin_offers'))


# ══════════════════════════════════════════════════════════════════════
#  Admin — Init DB
# ══════════════════════════════════════════════════════════════════════
@app.route('/admin/init-db')
@admin_required
def admin_init_db():
    db.create_all()
    _run_migrations()
    seed_products()
    flash('✅ Database initialised!', 'success')
    return redirect(url_for('admin_dashboard'))


# ══════════════════════════════════════════════════════════════════════
#  Startup Migrations
# ══════════════════════════════════════════════════════════════════════
def _run_migrations():
    sqls = [
        'ALTER TABLE products ADD COLUMN IF NOT EXISTS is_hidden BOOLEAN DEFAULT FALSE',
    ]
    try:
        with db.engine.connect() as conn:
            for sql in sqls:
                try:    conn.execute(db.text(sql))
                except: pass
            conn.commit()
    except Exception as e:
        print(f'[Migration] {e}')


with app.app_context():
    db.create_all()
    _run_migrations()
    seed_products()


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, use_reloader=True, port=5008)

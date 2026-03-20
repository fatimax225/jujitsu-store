# 🎁 Jujita Gifts — Full E-Commerce Website

A complete, production-ready e-commerce website for **Jujita Gifts**, a luxury gift store in Bahrain.
Built with **Flask (Python)** backend and a beautiful **HTML/CSS/JS** frontend.

---

## 🚀 Quick Start

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python app.py
```

### 3. Open in Browser
```
http://localhost:5000
```



---

## 📁 Project Structure

```
jujita_gifts/
├── app.py                        # Main Flask application
├── database.db                   # SQLite database (auto-created)
├── requirements.txt
├── static/
│   ├── css/
│   │   └── main.css              # Full luxury UI stylesheet
│   ├── js/
│   │   └── main.js               # Frontend interactions
│   └── images/
│       ├── default_product.jpg   # Fallback product image
│       └── uploads/              # Uploaded product & payment images
└── templates/
    ├── base.html                 # Shared navbar/footer layout
    ├── index.html                # Homepage with hero, featured, categories
    ├── products.html             # Product listing with filters
    ├── product_detail.html       # Product page with reviews
    ├── cart.html                 # Shopping cart
    ├── checkout.html             # Checkout form
    ├── order_confirmation.html   # Order placed + payment instructions
    ├── login.html                # Customer login
    ├── register.html             # Customer registration
    ├── about.html                # About page
    ├── contact.html              # Contact page
    └── admin/
        ├── base.html             # Admin layout with sidebar
        ├── login.html            # Admin login
        ├── dashboard.html        # Stats + recent orders
        ├── products.html         # Product list
        ├── product_form.html     # Add/Edit product form
        ├── orders.html           # All orders list
        ├── order_detail.html     # Single order + status update
        ├── users.html            # Customer list
        └── offers.html           # Discount offers manager
```

---

## ✨ Features

### Customer Side
- 🛍️ Browse products without login
- 🔍 Search by name + category filtering
- 🛒 Full cart system (add, update qty, remove)
- 📦 Place orders with delivery info
- 💳 BenefitPay payment instructions shown after order
- 📤 Upload payment proof screenshot
- ⭐ Write reviews and ratings (requires login)
- 🌐 Arabic / English language switch
- 📱 Fully responsive on mobile

### Admin Side
- 🔒 Private login at `/admin/login`
- 📊 Dashboard with revenue & stats
- ➕ Add / Edit / Delete products
  - Arabic + English names/descriptions
  - Image upload
  - Customizable options (e.g. colors, sizes)
  - Discount percentage
- 📋 View all orders with status management
- 👥 View customer data (name, phone, address)
- 🏷️ Manage offers/discounts

---

## 💳 Payment Flow

1. Customer places order → order saved in DB
2. Confirmation page shows:
   - **BenefitPay number: 34415700**
   - Total amount due
3. Customer uploads payment screenshot
4. Admin marks order as completed

---

## 🗄️ Database Tables

| Table | Fields |
|-------|--------|
| `users` | id, name, email, password, phone, address |
| `products` | id, name, name_ar, price, category, description, image, customizable_options, discount_percent, stock |
| `orders` | id, order_number, user_id, customer_name, customer_phone, customer_address, items, total_amount, status, payment_proof |
| `reviews` | id, product_id, user_id, user_name, rating, comment |
| `offers` | id, title, title_ar, description, discount_percent, category, active |

---

## 📞 Store Info

- **Phone / WhatsApp:** +973 3441 5700
- **BenefitPay:** 34415700

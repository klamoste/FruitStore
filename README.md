<<<<<<< HEAD
# 🍎 Fruit Store - Django E-Commerce System

A complete production-ready fruit store inventory and e-commerce system built with Django, featuring user authentication, product management, shopping cart, and order processing.

## 🚀 Features

### Authentication & Authorization
- User registration and login
- Role-based access control (Admin, Staff, Customer)
- User profile management
- Session-based authentication

### Product Management
- Product catalog with categories
- Product search and filtering (by category, price range)
- Product details with stock availability
- Category management
- Inventory logging (sale, restock, spoilage)
- Low stock alerts

### Shopping System
- Product listing with pagination
- Product detail pages
- Add to cart functionality (session-based)
- Cart management (update quantity, remove items)
- Search bar with live suggestions

### Order System
- Shopping cart with session storage
- Checkout process
- Order creation with automatic inventory deduction
- Order history tracking
- Order status management
- Order detail view

### Payment
- Simulated payment system
- Cash on Delivery (COD) option
- Mark as Paid option for admin

### Admin Dashboard
- Total sales and revenue
- Daily/weekly revenue analytics
- Order status breakdown
- Best-selling products
- Low stock alerts
- Quick admin actions

### User Interface
- Modern Shopee-inspired design
- Responsive Bootstrap 5 layout
- Professional navbar with navigation
- Product cards with images
- Shopping cart badge
- User dropdown menu
- Flash messages for user feedback

## 🛠️ Tech Stack

- **Backend**: Django 6.0+
- **Database**: SQLite (default, easily switchable to PostgreSQL)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Python**: 3.x

## 📦 Project Structure

```
fruit_store/
├── fruit_store/                    # Main project configuration
│   ├── settings.py                # Django settings
│   ├── urls.py                    # Main URL routing
│   ├── wsgi.py                    # WSGI configuration
│   └── asgi.py                    # ASGI configuration
├── accounts_app/                  # User authentication and profiles
│   ├── models.py                 # Profile model
│   ├── views.py                  # Register, Login, Logout, Profile
│   ├── forms.py                  # Authentication forms
│   ├── urls.py                   # App URLs
│   └── templates/accounts/       # Authentication templates
├── products_app/                  # Product management
│   ├── models.py                 # Product, Category, InventoryLog
│   ├── views.py                  # Product listing, detail, search
│   ├── forms.py                  # Product search and forms
│   ├── urls.py                   # App URLs
│   ├── templates/products/       # Product templates
│   └── management/commands/      # Custom Django commands
├── orders_app/                    # Order management
│   ├── models.py                 # Order, OrderItem
│   ├── views.py                  # Cart, Checkout, Order history
│   ├── forms.py                  # Payment and checkout forms
│   ├── urls.py                   # App URLs
│   └── templates/orders/         # Order templates
├── dashboard_app/                 # Admin dashboard
│   ├── views.py                  # Dashboard analytics
│   ├── urls.py                   # App URLs
│   └── templates/dashboard/      # Dashboard template
├── templates/                     # Project-wide templates
│   └── base.html                 # Base template with navbar
├── static/                        # Static files (CSS, JS, images)
│   ├── css/                      # Stylesheets
│   ├── js/                       # JavaScript files
│   └── images/                   # Images
├── media/                         # User-uploaded media (product images)
├── manage.py                      # Django management script
├── db.sqlite3                     # SQLite database
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 📋 Models

### accounts_app
- **Profile**: User profile with role selection (admin, staff, customer)

### products_app
- **Category**: Product categories (Fresh Fruits, Imported, etc.)
- **Product**: Product details with price, stock, images
- **InventoryLog**: Track inventory changes (sales, restocks, spoilage)

### orders_app
- **Order**: User orders with status and total price
- **OrderItem**: Individual items in an order

## 🔧 Installation & Setup

### 1. Navigate to Project Directory
```bash
cd c:\INVE\fruit_store\fruit_store
```

### 2. Install Dependencies
```bash
pip install -r ../requirements.txt
```

### 3. Create Database and Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Sample Data (Optional)
This command creates sample categories and products:
```bash
python manage.py create_sample_data
```

This creates:
- 5 product categories
- 8 sample products
- Admin user: `admin` / `admin123`
- Test customer: `testuser` / `testuser123`

### 5. Create Superuser (If not using sample data)
```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 6. Start Development Server
```bash
python manage.py runserver
```

The application will be available at: `http://127.0.0.1:8000/`

## 🌐 Application URLs

### Public Pages
- **Home**: `http://127.0.0.1:8000/` - Product listing
- **Product Detail**: `http://127.0.0.1:8000/product/<id>/` - View product details
- **Register**: `http://127.0.0.1:8000/accounts/register/` - Create new account
- **Login**: `http://127.0.0.1:8000/accounts/login/` - User login

### Authenticated User Pages
- **Cart**: `http://127.0.0.1:8000/orders/cart/` - Shopping cart
- **Checkout**: `http://127.0.0.1:8000/orders/checkout/` - Place order
- **Orders**: `http://127.0.0.1:8000/orders/orders/` - Order history
- **Profile**: `http://127.0.0.1:8000/accounts/profile/` - User profile

### Admin Pages
- **Admin Panel**: `http://127.0.0.1:8000/admin/` - Django admin
- **Dashboard**: `http://127.0.0.1:8000/dashboard/` - Analytics dashboard

## 👤 User Roles & Permissions

### Customer
- Browse products
- Search and filter products
- Add items to cart
- Place orders
- View order history
- Update profile

### Staff
- Access to admin panel
- Manage products
- View inventory
- Process orders

### Admin
- Full access to all features
- Manage users and roles
- View analytics dashboard
- Inventory management

## 🛒 Shopping Flow

1. **Browse Products**: Visit homepage to see product listings
2. **Search/Filter**: Use search bar or filters to find products
3. **View Details**: Click on product to see details and stock
4. **Add to Cart**: Add items with desired quantity
5. **View Cart**: Review items and make changes
6. **Checkout**: Select payment method and place order
7. **Order Confirmation**: View order confirmation and status
8. **Track Order**: Check order history page for status updates

## 💳 Payment Methods

- **Cash on Delivery**: Pay when order arrives
- **Mark as Paid**: Admin can manually mark orders as paid

## 📊 Admin Dashboard Features

- Total orders and revenue
- Daily revenue tracking
- Best-selling products
- Low stock alerts
- Order status breakdown
- Quick admin actions

## 🔄 Inventory Management

- Automatic stock deduction on purchase
- Low stock alerts (< 10 items)
- Inventory logging (sales, restocks, spoilage)
- FIFO simulation support

## 🎨 UI/UX Features

- Modern Shopee-inspired design
- Responsive Bootstrap 5 layout
- Professional product cards
- Shopping cart badge
- Flash messages for feedback
- Breadcrumb navigation
- Modal dialogs
- Smooth animations

## 📱 Responsive Design

- Mobile-friendly interface
- Touch-optimized buttons
- Responsive grid layout
- Adaptive navigation

## 🔒 Security Features

- CSRF protection
- User authentication
- Role-based access control
- Session management
- Password hashing

## 🚀 Production Deployment

### Switch to PostgreSQL
1. Install PostgreSQL
2. Update `settings.py` DATABASES:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'fruit_store_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Update Security Settings
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 🐛 Troubleshooting

### Import Errors
- Ensure all apps are added to `INSTALLED_APPS` in settings.py
- Check app names match the directory names

### Database Errors
- Run migrations: `python manage.py migrate`
- Clear old migrations if needed: `python manage.py makemigrations --clear`

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Check STATIC_ROOT and STATIC_URL in settings

### Cart Not Working
- Clear browser cookies
- Check Django session backend in settings

## 📝 Notes

- Product images should be uploaded through Django admin
- Cart is stored in session - no persistent storage between logins
- Order data is permanently stored in the database
- Inventory logs all sales for tracking

## 🤝 Contributing

Feel free to extend this project with additional features:
- Email notifications
- Advanced search filters
- Wishlist functionality
- Product reviews and ratings
- Coupon/discount system
- Wishlist
- Payment gateway integration

## 📄 License

This is a demonstration project for educational purposes.

## 👨‍💻 Support

For issues or questions, check the Django documentation:
- Django Docs: https://docs.djangoproject.com/
- Bootstrap Docs: https://getbootstrap.com/

## 📈 Performance Tips

- Use database indexes on frequently searched fields
- Enable query caching for product listings
- Use CDN for static files in production
- Optimize images before upload
- Implement pagination for large datasets
- Use Django's cache framework

---

**Version**: 1.0.0  
**Last Updated**: April 2026  
**Status**: Production Ready ✅
=======
# FruitStore
fruits
>>>>>>> b6c7887870a81fa809195598fca7fe2e91de99b3

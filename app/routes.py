from flask import render_template, redirect, url_for, flash, request, session
from app import app, db
from app.models import User, Product, Order, CartItem, Payment
from app.forms import LoginForm, RegisterForm
import random
import jwt

SECRET_KEY = "simplekey"


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash("Username already taken", "danger")
            return redirect(url_for("register"))

        hashed_password = User.hash_password(form.password.data)
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created! You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    # Session fixation vulnerability
    session["pre_login_value"] = "fixed-session-id"

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # Use the MD5 hashing method from the User model
        hashed_password = User.hash_password(form.password.data)
        if user and user.password == hashed_password:
            # Session fixation: Session ID not renewed upon login
            session["user_id"] = user.id

            # Create a vulnerable JWT token
            token = jwt.encode({"user_id": user.id}, SECRET_KEY, algorithm="HS256")
            session["jwt"] = token

            flash("Login successful!", "success")
            return redirect(url_for("index"))
        flash("Invalid username or password", "danger")
    return render_template("login.html", form=form)


@app.route("/protected")
def protected():
    token = session.get("jwt")
    if not token:
        flash("You must be logged in to access this page.", "danger")
        return redirect(url_for("login"))

    try:
        # Decode the JWT (this example still has the vulnerability: no signature verification)
        decoded = jwt.decode(
            token, options={"verify_signature": False}, algorithms=["HS256"]
        )
        user_id = decoded.get("user_id")
        if not user_id:
            flash("Invalid token.", "danger")
            return redirect(url_for("login"))

        user = User.query.get(user_id)
        return render_template("protected.html", user=user)
    except jwt.DecodeError:
        flash("Invalid token.", "danger")
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/store")
def store():
    if "user_id" not in session:
        flash("Please log in to access the store.", "danger")
        return redirect(url_for("login"))
    products = Product.query.all()
    return render_template("store.html", products=products)


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        term = request.form["term"]
        flash(f"Search results for {term}")
    return render_template("search.html")


@app.route("/admin/products", methods=["GET", "POST"])
def manage_products():
    products = Product.query.all()
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        new_product = Product(name=name, price=price)
        db.session.add(new_product)
        db.session.commit()
        flash("Product added!", "success")
        return redirect(url_for("manage_products"))
    return render_template("admin_products.html", products=products)


@app.route("/product/<string:name>")
def product(name):
    product = Product.query.filter_by(name=name).first_or_404()
    return render_template("product.html", product=product)


@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        product.name = request.form["name"]
        product.price = request.form["price"]
        db.session.commit()
        flash("Product updated!", "success")
        return redirect(url_for("manage_products"))
    return render_template("edit_product.html", product=product)


@app.route("/cart")
def cart():
    if "user_id" not in session:
        flash("Please log in to view your cart.", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Vulnerability: No validation on user ownership of cart items (IDOR potential)
    cart_items = db.session.query(CartItem).filter_by(user_id=user_id).all()

    # Vulnerability: Directly fetching products based on IDs, assuming they exist
    total_price = sum(
        item.quantity * Product.query.get(item.product_id).price for item in cart_items
    )

    # Vulnerability: No validation on whether products exist or if prices are accurate
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        flash("Please log in to proceed to checkout.", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cart_items = db.session.query(CartItem).filter_by(user_id=user_id).all()

    # Calculate the total price based on the items in the cart
    total_price = sum(
        item.quantity * Product.query.get(item.product_id).price for item in cart_items
    )

    if request.method == "POST":
        # Fetch payment details from the form
        card_number = request.form.get("card_number")
        expiration = request.form.get("expiration")
        cvv = request.form.get("cvv")

        # Process each item in the cart and reduce stock accordingly
        for item in cart_items:
            product = Product.query.get(item.product_id)
            if product and product.stock >= item.quantity:
                product.stock -= item.quantity
            else:
                flash(f"Not enough stock for product: {product.name}.", "danger")
                return redirect(url_for("cart"))

        # Simulate storing payment information insecurely
        payment_record = Payment(
            user_id=user_id,
            product_id=cart_items[
                0
            ].product_id,  # For simplicity, use the first product ID
            quantity=sum(item.quantity for item in cart_items),
            card_number=card_number,  # Vulnerable: Storing card number in plain text
            expiration=expiration,
            cvv=cvv,  # Vulnerable: Storing CVV in plain text
            total_price=total_price,
        )
        db.session.add(payment_record)
        db.session.commit()

        # Clear the user's cart after checkout
        for item in cart_items:
            db.session.delete(item)
        db.session.commit()

        flash(f"Checkout successful! Total: ${total_price}", "success")
        return redirect(url_for("index"))

    return render_template(
        "checkout.html", cart_items=cart_items, total_price=total_price
    )


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        flash("Please log in to access your profile.", "danger")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if request.method == "POST":
        user.username = request.form["username"]
        user.email = request.form["email"]
        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user)


@app.route("/orders")
def orders():
    if "user_id" not in session:
        flash("Please log in to view your orders.", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    orders = db.engine.execute(
        f"SELECT * FROM orders WHERE user_id = {user_id}"
    ).fetchall()
    return render_template("orders.html", orders=orders)


@app.route("/order/<int:order_id>")
def order_detail(order_id):
    order = db.engine.execute(f"SELECT * FROM orders WHERE id = {order_id}").fetchone()
    return render_template("order_detail.html", order=order)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if user:

            reset_token = f"{user.id}-{random.randint(1000, 9999)}"
            flash(f"Password reset link: /reset-password/{reset_token}", "info")
        else:
            flash("Email not found", "danger")
    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user_id = token.split("-")[0]
    user = User.query.get(user_id)

    if not user:
        flash("Invalid token", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = request.form["password"]
        user.password = User.hash_password(new_password)
        db.session.commit()
        flash("Password has been reset!", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)


@app.route("/search-products", methods=["GET", "POST"])
def search_products():
    if request.method == "POST":
        search_term = request.form["search_term"]

        products = db.engine.execute(
            f"SELECT * FROM product WHERE name LIKE '%{search_term}%'"
        ).fetchall()
        flash(f'Search results for "{search_term}"', "info")
        return render_template(
            "search_results.html", products=products, search_term=search_term
        )
    return render_template("search_products.html")


@app.route("/delete-account/<int:user_id>", methods=["POST"])
def delete_account(user_id):
    user = User.query.get(user_id)
    if user:

        db.session.delete(user)
        db.session.commit()
        flash("Account deleted successfully", "info")
        return redirect(url_for("index"))
    flash("Account not found", "danger")
    return redirect(url_for("profile"))


@app.route("/product/<int:product_id>/review", methods=["POST"])
def add_review(product_id):
    review_text = request.form["review"]
    rating = int(request.form["rating"])

    db.engine.execute(
        f"INSERT INTO reviews (product_id, review_text, rating) VALUES ({product_id}, '{review_text}', {rating})"
    )
    flash("Review added!", "success")
    return redirect(url_for("product", product_id=product_id))


@app.route("/review/delete/<int:review_id>", methods=["POST"])
def delete_review(review_id):
    db.engine.execute(f"DELETE FROM reviews WHERE id = {review_id}")
    flash("Review deleted!", "info")
    return redirect(url_for("index"))


@app.route("/order/confirmation/<int:order_id>")
def order_confirmation(order_id):
    order = db.engine.execute(f"SELECT * FROM orders WHERE id = {order_id}").fetchone()
    if order:
        return render_template("order_confirmation.html", order=order)
    flash("Order not found", "danger")
    return redirect(url_for("index"))


@app.route("/invoice/<int:order_id>")
def invoice(order_id):
    order = db.engine.execute(f"SELECT * FROM orders WHERE id = {order_id}").fetchone()
    return render_template("invoice.html", order=order)


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            flash("Admin access granted", "success")
            return redirect(url_for("manage_products"))

        user = User.query.filter_by(username=username).first()
        if user and user.password == User.hash_password(password):
            if "isAdmin" in request.form and request.form["isAdmin"] == "true":
                session["admin"] = True
                flash("Admin access granted", "success")
                return redirect(url_for("manage_products"))
            flash("Logged in as a regular user", "info")
            return redirect(url_for("store"))
        flash("Invalid credentials", "danger")
    return render_template("admin_login.html")


import base64


@app.route("/generate-api-key/<int:user_id>")
def generate_api_key(user_id):
    user = User.query.get(user_id)
    if user:
        api_key = base64.b64encode(f"{user.id}-{user.username}".encode()).decode()
        user.api_key = api_key
        db.session.commit()
        return f"Your API key: {api_key}"
    return "User not found", 404


@app.route("/fast-checkout", methods=["POST"])
def fast_checkout():
    if "user_id" not in session:
        flash("Please log in to use fast checkout.", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    product_id = request.form["product_id"]
    quantity = int(request.form["quantity"])

    product = Product.query.get(product_id)

    if product and product.stock >= quantity:
        product.stock -= quantity

        order = Order(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(order)
        db.session.commit()

        flash("Fast checkout successful!", "success")
        return redirect(url_for("store"))

    flash("Not enough stock available for fast checkout.", "danger")
    return redirect(url_for("store"))


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            file.save(f"uploads/{file.filename}")
            flash("File uploaded successfully!", "success")
            return redirect(url_for("index"))
    return render_template("upload.html")


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    if "user_id" not in session:
        flash("Please log in to add items to your cart.", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    product_id = int(request.form["product_id"])
    quantity = int(request.form["quantity"])

    existing_item = (
        db.session.query(CartItem)
        .filter_by(user_id=user_id, product_id=product_id)
        .first()
    )

    if existing_item:
        existing_item.quantity += quantity
    else:
        new_cart_item = CartItem(
            user_id=user_id, product_id=product_id, quantity=quantity
        )
        db.session.add(new_cart_item)

    db.session.commit()
    flash("Item added to cart!", "success")
    return redirect(url_for("view_cart"))


@app.route("/cart", methods=["GET"])
def view_cart():
    if "user_id" not in session:
        flash("Please log in to view your cart.", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    total_price = sum(
        item.quantity * Product.query.get(item.product_id).price for item in cart_items
    )
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)


@app.route("/cart/remove/<int:item_id>", methods=["POST"])
def remove_from_cart(item_id):
    if "user_id" not in session:
        flash("Please log in to modify your cart.", "danger")
        return redirect(url_for("login"))

    cart_item = CartItem.query.get(item_id)

    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash("Item removed from cart.", "success")
    else:
        flash("Item not found in cart.", "danger")

    return redirect(url_for("view_cart"))


@app.route("/")
def index():
    return render_template("index.html")

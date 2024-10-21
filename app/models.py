from app import db
import hashlib
import argon2
import logging

logger = logging.getLogger(__name__)


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
    )
    password = db.Column(db.String(60), nullable=False)
    cart_items = db.relationship("CartItem", backref="user", lazy=True)

    @staticmethod
    def hash_password(password):
        # Use Argon2 for password hashing
        try:
            return argon2.PasswordHasher().hash(password)
        except argon2.exceptions.HashingError as e:
            logging.basicConfig(filename=f"{__name__}.log", level=logging.ERROR)
            logger.info(f"Password hashing failed: {e}")
            raise ValueError("Password hashing failed") from e


class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    stock = db.Column(db.Integer, nullable=False, default=0)  # Stock availability


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


class CartItem(db.Model):
    __tablename__ = "cart_item"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # Establish a relationship with the Product model
    product = db.relationship("Product", backref="cart_items", lazy=True)


class Payment(db.Model):
    __tablename__ = "payment"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    card_number = db.Column(db.String(20), nullable=False)
    expiration = db.Column(db.String(5), nullable=False)
    cvv = db.Column(db.String(4), nullable=False)
    total_price = db.Column(db.Float, nullable=False)

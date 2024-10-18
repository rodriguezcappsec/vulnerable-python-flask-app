from app import app, db
from app.models import CartItem, User, Product  # Import all models


def init_db():
    with app.app_context():
        db.create_all()

        # Add some initial products and users
        product1 = Product(name="Flask Vulnerability Book", price=29.99)
        product2 = Product(name="Hacker T-shirt", price=19.99)
        db.session.add_all([product1, product2])

        user1 = User(
            username="admin", email="admin@example.com", password="password123"
        )
        db.session.add(user1)

        db.session.commit()
        print("Database initialized with sample data!")


if __name__ == "__main__":
    init_db()

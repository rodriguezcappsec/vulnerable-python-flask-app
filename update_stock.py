from app import app, db
from app.models import Product

with app.app_context():
    products = Product.query.all()
    for product in products:
        product.stock = 10  # Set a default stock level for all products
    db.session.commit()
    print("Stock levels updated!")

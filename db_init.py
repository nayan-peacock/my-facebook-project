from backend import create_app, db
from backend.models import * # Import all models so SQLAlchemy knows about them

app = create_app()

with app.app_context():
    print("Dropping existing tables (if any)...")
    db.drop_all()
    print("Creating new tables...")
    db.create_all()
    print("Database has been initialized! ✨")
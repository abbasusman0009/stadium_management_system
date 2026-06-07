from flask import Flask, render_template, redirect, url_for, request, flash
from extensions import db, bcrypt, login_manager
from config import Config
from models import User, Event, Seat, Booking, Payment, Ticket
from auth import auth_bp
from admin import admin_bp
from booking import booking_bp
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(booking_bp, url_prefix='/booking')
    
    # Ensure standard directories exist for storing QR codes and uploads
    os.makedirs(os.path.join(app.root_path, 'static', 'qrcodes'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'uploads'), exist_ok=True)

    with app.app_context():
        db.create_all()
        # Create a default admin user if not exists
        if not User.query.filter_by(email='admin@stadium.com').first():
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(name='System Admin', email='admin@stadium.com', password_hash=hashed_password, role='admin')
            db.session.add(admin)
            db.session.commit()

    # --- ROUTES ---
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def home():
        events = Event.query.order_by(Event.date.asc()).all()
        return render_template('home.html', events=events)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

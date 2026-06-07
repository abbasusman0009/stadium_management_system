from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user') # 'user' or 'admin'
    
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    seats = db.relationship('Seat', backref='event', lazy=True, cascade="all, delete-orphan")

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seat_no = db.Column(db.String(20), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available') # available, locked, booked
    price = db.Column(db.Float, nullable=False, default=0.0)
    
    bookings = db.relationship('Booking', backref='seat', lazy=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') # pending, success, failed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    booking = db.relationship('Booking', backref='payment', uselist=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending') # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    ticket = db.relationship('Ticket', backref='booking', uselist=False)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    qr_code_path = db.Column(db.String(255), nullable=True)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

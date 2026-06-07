from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Event, Seat, Booking, Payment, Ticket
import qrcode
import os
import uuid

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/event/<int:event_id>')
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    seats = Seat.query.filter_by(event_id=event.id).all()
    
    # Calculate stats
    total_seats = len(seats)
    available_seats = len([s for s in seats if s.status == 'available'])
    
    return render_template('event_details.html', event=event, seats=seats, available_seats=available_seats, total_seats=total_seats)

@booking_bp.route('/book/<int:seat_id>', methods=['POST'])
@login_required
def book_seat(seat_id):
    seat = Seat.query.get_or_404(seat_id)
    
    if seat.status != 'available':
        flash('Sorry, this seat is no longer available.', 'danger')
        return redirect(url_for('booking.event_details', event_id=seat.event_id))
        
    # Lock the seat
    seat.status = 'locked'
    db.session.commit()
    
    # Create pending booking
    booking = Booking(user_id=current_user.id, seat_id=seat.id)
    db.session.add(booking)
    db.session.commit()
    
    return redirect(url_for('booking.checkout', booking_id=booking.id))

@booking_bp.route('/checkout/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def checkout(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user.id or booking.status != 'pending':
        flash('Invalid booking.', 'danger')
        return redirect(url_for('home'))
        
    seat = Seat.query.get(booking.seat_id)
    
    if request.method == 'POST':
        # Mock Payment Processing
        payment = Payment(
            amount=seat.price,
            reference=str(uuid.uuid4()),
            status='success'
        )
        db.session.add(payment)
        db.session.flush() # Get payment.id
        
        # Update booking & seat
        booking.payment_id = payment.id
        booking.status = 'confirmed'
        seat.status = 'booked'
        
        # Generate Ticket
        ticket = Ticket(booking_id=booking.id)
        db.session.add(ticket)
        db.session.flush()
        
        # Generate QR Code
        qr_data = f"TicketID:{ticket.id}|BookingRef:{payment.reference}"
        img = qrcode.make(qr_data)
        
        # Ensure directory exists (already done in app.py, but safe to assume it's there)
        from flask import current_app
        filename = f"qr_{ticket.id}.png"
        filepath = os.path.join(current_app.root_path, 'static', 'qrcodes', filename)
        img.save(filepath)
        
        ticket.qr_code_path = f"qrcodes/{filename}"
        db.session.commit()
        
        flash('Payment successful! Your ticket has been generated.', 'success')
        return redirect(url_for('booking.view_ticket', ticket_id=ticket.id))
        
    return render_template('checkout.html', booking=booking, seat=seat)

@booking_bp.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    booking = Booking.query.get(ticket.booking_id)
    
    if booking.user_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to view this ticket.', 'danger')
        return redirect(url_for('home'))
        
    event = Event.query.get(booking.seat.event_id)
    
    return render_template('ticket.html', ticket=ticket, booking=booking, event=event)

@booking_bp.route('/my-tickets')
@login_required
def my_tickets():
    bookings = Booking.query.filter_by(user_id=current_user.id, status='confirmed').order_by(Booking.created_at.desc()).all()
    return render_template('my_tickets.html', bookings=bookings)

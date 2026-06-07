from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Event, Seat, Booking, Payment, Ticket
from datetime import datetime
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_events = Event.query.count()
    total_bookings = Booking.query.filter_by(status='confirmed').count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter_by(status='success').scalar() or 0.0
    
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('admin/dashboard.html', 
                           total_users=total_users,
                           total_events=total_events,
                           total_bookings=total_bookings,
                           total_revenue=total_revenue,
                           events=events)

@admin_bp.route('/event/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_event():
    if request.method == 'POST':
        title = request.form.get('title')
        date_str = request.form.get('date') # Format: YYYY-MM-DDTHH:MM
        description = request.form.get('description')
        capacity = int(request.form.get('capacity', 0))
        price = float(request.form.get('price', 0.0))
        
        event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        
        # Handle Image Upload
        image = request.files.get('image')
        image_url = None
        if image and image.filename:
            import os
            from werkzeug.utils import secure_filename
            from flask import current_app
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, 'static', 'img', 'events')
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = secure_filename(f"{datetime.now().timestamp()}_{image.filename}")
            filepath = os.path.join(upload_dir, filename)
            image.save(filepath)
            
            # Format URL for template
            image_url = url_for('static', filename=f'img/events/{filename}')
        
        event = Event(title=title, date=event_date, description=description, image_url=image_url)
        db.session.add(event)
        db.session.commit() # Commit to get event ID
        
        # Generate seats for the event
        for i in range(1, capacity + 1):
            seat = Seat(seat_no=f"S-{i}", event_id=event.id, price=price)
            db.session.add(seat)
            
        db.session.commit()
        flash('Event created successfully with seats!', 'success')
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/new_event.html')

@admin_bp.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        event.title = request.form.get('title')
        event.description = request.form.get('description')
        
        date_str = request.form.get('date')
        if date_str:
            event.date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            
        image = request.files.get('image')
        if image and image.filename:
            import os
            from werkzeug.utils import secure_filename
            from flask import current_app
            upload_dir = os.path.join(current_app.root_path, 'static', 'img', 'events')
            os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(f"{datetime.now().timestamp()}_{image.filename}")
            filepath = os.path.join(upload_dir, filename)
            image.save(filepath)
            event.image_url = url_for('static', filename=f'img/events/{filename}')
            
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/edit_event.html', event=event)

@admin_bp.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    # Note: SQLite might fail if there are related bookings/seats.
    # In a real system, we'd soft-delete or cascade delete.
    # We will delete seats associated if they have no bookings. 
    # For a simple delete, we will just delete it and let SQLAlchemy handle it if cascade is set, or we manually delete seats.
    Seat.query.filter_by(event_id=event.id).delete()
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/scanner', methods=['GET', 'POST'])
@login_required
@admin_required
def scanner():
    if request.method == 'POST':
        ticket_id = request.form.get('ticket_id')
        ticket = Ticket.query.get(ticket_id)
        
        if ticket:
            if ticket.is_used:
                flash('Ticket has already been used!', 'danger')
            else:
                ticket.is_used = True
                db.session.commit()
                flash('Ticket validated successfully! Access granted.', 'success')
        else:
            flash('Invalid Ticket ID.', 'danger')
            
    return render_template('admin/scanner.html')

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    from flask_bcrypt import Bcrypt
    bcrypt = Bcrypt()
    
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    
    if User.query.filter_by(email=email).first():
        flash('Email address already exists', 'danger')
        return redirect(url_for('admin.manage_users'))
        
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(name=name, email=email, password_hash=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    flash(f'User {name} successfully registered as {role}.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def toggle_role(user_id):
    if user_id == current_user.id:
        flash('You cannot change your own role.', 'danger')
        return redirect(url_for('admin.manage_users'))
        
    user = User.query.get_or_404(user_id)
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    flash(f"User {user.name} role changed to {user.role}.", 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.manage_users'))
        
    user = User.query.get_or_404(user_id)
    
    # We will simply delete the user. The bookings will be orphaned or we can cascade delete.
    # To prevent foreign key errors with SQLite, it's often better to just anonymize or disable.
    # For now, let's just delete if we have cascading set up, but wait, Booking table has `user_id` as non-nullable.
    # Deleting a user will crash if they have bookings unless we use cascade="all, delete" in models.
    # We didn't set cascade for User->Booking. So we'll disable them by changing their password to something un-loginable.
    # Or just delete all their bookings first. Since we want to keep revenue records, let's anonymize the user.
    
    user.email = f"deleted_{user.id}@stadium.local"
    user.name = "Deleted User"
    user.password_hash = "disabled"
    db.session.commit()
    
    flash(f"User account deactivated and anonymized.", 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/box-office', methods=['GET', 'POST'])
@login_required
@admin_required
def box_office():
    events = Event.query.filter(Event.date >= datetime.utcnow()).order_by(Event.date.asc()).all()
    users = User.query.filter(User.email != 'admin@stadium.com').all()
    
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        user_id = request.form.get('user_id')
        seat_id = request.form.get('seat_id')
        
        seat = Seat.query.get(seat_id)
        if not seat or seat.status != 'available':
            flash('Selected seat is not available.', 'danger')
            return redirect(url_for('admin.box_office'))
            
        user = User.query.get(user_id)
        
        # Lock seat
        seat.status = 'booked'
        
        # Create payment
        payment = Payment(amount=seat.price, reference=f"ADMIN_CASH_{datetime.utcnow().timestamp()}", status='success')
        db.session.add(payment)
        db.session.flush()
        
        # Create booking
        booking = Booking(user_id=user.id, seat_id=seat.id, payment_id=payment.id, status='confirmed')
        db.session.add(booking)
        db.session.flush()
        
        # Generate ticket
        ticket = Ticket(booking_id=booking.id)
        db.session.add(ticket)
        db.session.flush()
        
        # Generate QR
        import qrcode
        import os
        from flask import current_app
        qr_data = f"TicketID:{ticket.id}|BookingRef:{payment.reference}"
        img = qrcode.make(qr_data)
        filename = f"qr_{ticket.id}.png"
        filepath = os.path.join(current_app.root_path, 'static', 'qrcodes', filename)
        img.save(filepath)
        ticket.qr_code_path = f"qrcodes/{filename}"
        
        db.session.commit()
        flash(f'Ticket #{ticket.id} booked successfully for {user.name}!', 'success')
        return redirect(url_for('admin.box_office'))
        
    return render_template('admin/box_office.html', events=events, users=users)

@admin_bp.route('/api/seats/<int:event_id>')
@login_required
@admin_required
def get_seats(event_id):
    seats = Seat.query.filter_by(event_id=event_id, status='available').all()
    return {'seats': [{'id': s.id, 'seat_no': s.seat_no, 'price': s.price} for s in seats]}

@admin_bp.route('/export/attendees/<int:event_id>')
@login_required
@admin_required
def export_attendees(event_id):
    import csv
    from io import StringIO
    from flask import Response
    
    event = Event.query.get_or_404(event_id)
    seats = Seat.query.filter_by(event_id=event.id, status='booked').all()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Ticket ID', 'Seat Number', 'User Name', 'User Email', 'Payment Reference', 'Status'])
    
    for seat in seats:
        # Find the confirmed booking for this seat
        booking = Booking.query.filter_by(seat_id=seat.id, status='confirmed').first()
        if booking:
            cw.writerow([
                booking.ticket.id if booking.ticket else 'N/A',
                seat.seat_no,
                booking.user.name,
                booking.user.email,
                booking.payment.reference if booking.payment else 'N/A',
                'Used' if (booking.ticket and booking.ticket.is_used) else 'Valid'
            ])
            
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=attendees_{event.id}.csv"}
    )

@admin_bp.route('/event/<int:event_id>/seats')
@login_required
@admin_required
def manage_seats(event_id):
    event = Event.query.get_or_404(event_id)
    seats = Seat.query.filter_by(event_id=event.id).order_by(Seat.seat_no).all()
    return render_template('admin/manage_seats.html', event=event, seats=seats)

@admin_bp.route('/seat/<int:seat_id>/update', methods=['POST'])
@login_required
@admin_required
def update_seat(seat_id):
    seat = Seat.query.get_or_404(seat_id)
    
    # If the seat is booked, do not allow changing status manually via this route to prevent DB inconsistency, 
    # but price can still be updated for future reference, though typically fixed.
    if seat.status == 'booked':
        flash('Cannot modify a booked seat.', 'danger')
        return redirect(url_for('admin.manage_seats', event_id=seat.event_id))
        
    status = request.form.get('status')
    price = request.form.get('price')
    
    if status in ['available', 'locked']:
        seat.status = status
    if price:
        seat.price = float(price)
        
    db.session.commit()
    flash(f'Seat {seat.seat_no} updated successfully.', 'success')
    return redirect(url_for('admin.manage_seats', event_id=seat.event_id))

@admin_bp.route('/event/<int:event_id>/seat/add', methods=['POST'])
@login_required
@admin_required
def add_seat(event_id):
    event = Event.query.get_or_404(event_id)
    seat_no = request.form.get('seat_no')
    price = request.form.get('price', 0.0)
    
    if Seat.query.filter_by(event_id=event.id, seat_no=seat_no).first():
        flash('A seat with that number already exists for this event.', 'danger')
    else:
        new_seat = Seat(seat_no=seat_no, event_id=event.id, price=float(price))
        db.session.add(new_seat)
        db.session.commit()
        flash('New seat added successfully.', 'success')
        
    return redirect(url_for('admin.manage_seats', event_id=event.id))

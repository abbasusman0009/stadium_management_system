# System Implementation Details for Chapter Four & Five

This document provides all the technical details, database structures, and implemented features of the **Web-Based Stadium Management System** we built. You can use this exact information to write Chapter Four (Implementation and Testing) and Chapter Five (Summary, Conclusion, and Recommendation) for your project defense.

---

## 1. Technologies Used
- **Backend Framework:** Python with Flask (A lightweight and powerful WSGI web application framework).
- **Database:** SQLite (A C-language library that implements a small, fast, self-contained SQL database engine), managed via **Flask-SQLAlchemy** (Object Relational Mapper).
- **Frontend Presentation:** HTML5, CSS3 (Vanilla CSS with a custom responsive Red, White, and Blue theme), and Jinja2 Templating Engine.
- **Authentication:** Flask-Login for session management and Flask-Bcrypt for secure password hashing.
- **Ticketing & QR Codes:** Python `qrcode` library for generating scannable digital tickets.
- **Routing & Architecture:** Modular Blueprint architecture separating `auth`, `admin`, and `booking` logic.

---

## 2. Database Structure (Tables & Schema)
The system uses a relational database with the following actual tables:

### A. `user` Table
Stores all registered users and administrators.
- `id` (Integer, Primary Key)
- `name` (String, max 100 characters)
- `email` (String, max 120 characters, Unique)
- `password_hash` (String, length 60 - Bcrypt hashed)
- `role` (String, default: 'user' | 'admin')

### B. `event` Table
Stores all stadium events (matches, concerts, etc.).
- `id` (Integer, Primary Key)
- `title` (String, max 150)
- `description` (Text)
- `date` (DateTime)
- `image_url` (String, max 200 - Path to uploaded event banner)
- *Relationship*: One-to-Many with `Seat`.

### C. `seat` Table
Represents individual physical seats inside the stadium for a specific event.
- `id` (Integer, Primary Key)
- `seat_no` (String, max 20)
- `price` (Float)
- `status` (String: 'available', 'booked', or 'locked')
- `event_id` (Integer, Foreign Key to `event.id`)

### D. `payment` Table
Logs all financial transactions (both online and admin cash bookings).
- `id` (Integer, Primary Key)
- `amount` (Float)
- `reference` (String, max 100, Unique - e.g., "ADMIN_CASH_12345")
- `status` (String: 'pending', 'success', 'failed')
- `created_at` (DateTime)

### E. `booking` Table
Links a User, a Seat, and a Payment together.
- `id` (Integer, Primary Key)
- `user_id` (Integer, Foreign Key to `user.id`)
- `seat_id` (Integer, Foreign Key to `seat.id`)
- `payment_id` (Integer, Foreign Key to `payment.id`)
- `status` (String: 'pending', 'confirmed', 'cancelled')
- `created_at` (DateTime)

### F. `ticket` Table
The final generated digital ticket with a scannable QR Code.
- `id` (Integer, Primary Key)
- `booking_id` (Integer, Foreign Key to `booking.id`)
- `qr_code_path` (String, max 200)
- `is_used` (Boolean, Default: False - toggled by the Admin Scanner)
- `issued_at` (DateTime)

---

## 3. Modules Developed (Actual Implementation)

### 3.1 Authentication & Profile Module
- Registration and Login with Bcrypt password encryption.
- A "My Profile" page where users can update their display names and securely change passwords.

### 3.2 Admin Dashboard & Event Management
- Admins can view high-level metrics (Total Revenue, Tickets Sold, Total Users).
- **Create Event**: Admins can upload an image, set a date, and define the seat capacity. The system automatically loops and generates the exact number of physical seat records in the database.
- **Manage Seats**: Admins can manually add new seats to an existing event (e.g., VIP rows), lock seats to prevent online booking, or adjust prices.

### 3.3 User Booking & "My Tickets" Module
- Users browse a homepage of upcoming events.
- An interactive seat selection page showing only `available` seats.
- A mock Paystack payment gateway integration page.
- A "My Tickets" portal where users view all past/present tickets and download their unique QR Codes.

### 3.4 Box Office Module (Admin)
- Developed specifically for cash sales at the stadium gate.
- Admins can select an event, an available seat, and a registered user to instantly generate a confirmed booking and ticket, bypassing the online payment gateway.

### 3.5 Validation & Security Module
- **Ticket Scanner**: A dedicated admin page where tickets are validated using their unique ID. Once scanned, `is_used` becomes `True`, physically preventing ticket duplication or reuse at the gates.
- **Data Export**: Admins can export a CSV report of all attendees for a specific event, showing who has checked in (Status: Used) and who hasn't (Status: Valid).

---

## 4. Testing Results

During implementation, the following test cases were validated successfully:
1. **Concurrency/Double Booking Test**: If two users attempt to book the exact same seat simultaneously, the system prevents the second user because the seat status locks immediately upon the first successful payment.
2. **Authentication Validation**: Attempting to access `/admin/dashboard` as a normal user successfully redirects the user away with a "Permission Denied" flash message.
3. **Ticket Validation**: Inputting a Ticket ID into the scanner twice successfully returns a "Ticket has already been used!" error on the second attempt.
4. **File Upload Security**: Event image uploads successfully utilize `secure_filename()` to prevent directory traversal attacks.

---

## 5. Challenges Encountered
*(You can include these in Chapter 4)*
1. **Dynamic Seat Generation**: Handling the creation of hundreds of individual seat records in the database simultaneously when an event is created required careful database session management to prevent timeouts.
2. **UI Theme Transformation**: Adapting the initial dark-mode CSS to a clean, highly legible Red, White, and Blue theme required meticulous updates to CSS variables and overriding hardcoded text colors without breaking the glassmorphism aesthetic.
3. **Foreign Key Constraints**: Designing the "Deactivate User" functionality. Hard-deleting a user would crash the system due to tied financial booking records. The challenge was solved by anonymizing deactivated users (changing their email to `deleted_ID` and password to `disabled`) to preserve accurate revenue analytics.

---

## 6. Required Screenshots for your Report
To make your report perfect, use a Snipping Tool to take screenshots of the system running on your laptop. Make sure to capture:
1. **The Homepage** (showing the Red, White, and Blue theme and event cards).
2. **The Login/Register Page**.
3. **The Admin Dashboard** (showing the Total Revenue and Events table).
4. **The Create Event Page** (showing the Image Upload field).
5. **The Manage Users Page** (showing the Admin Registration form).
6. **The Box Office Page**.
7. **A User's "My Tickets" Page**.
8. **The Final Digital Ticket** (showing the QR Code).

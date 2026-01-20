"""
FLYTAU - Flight management web application (Final Project)

This Flask app manages flights, bookings, and staff/aircraft assignments.
Main rules enforced in the system:
- Flights have statuses (Active/Full/Performed/Cancelled).
- Only eligible resources (aircraft/crew) can be assigned based on time overlap and location continuity.
- "Append-only" continuity: an aircraft/crew can only be scheduled for the NEXT flight that departs
  from the last destination they will reach in their current schedule chain.
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from contextlib import contextmanager  # ✅ NEW
import random
import string
import re
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'database': os.getenv('DB_NAME')
}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


class DBManager:
    """Small helper class for running MySQL queries and returning dict-based rows."""

    def __init__(self, config):
        self.config = config

    @contextmanager
    def _cursor(self, dictionary=True):
        """
        Context manager that opens a DB connection + cursor and ALWAYS closes them.
        Commits on success, rollbacks on error.
        """
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=dictionary)
            yield conn, cursor
            conn.commit()
        except mysql.connector.Error:
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_query(self, query, params=None):
        """
        Execute INSERT/UPDATE/DELETE.
        Returns lastrowid for INSERT, or None on failure.
        """
        try:
            with self._cursor(dictionary=True) as (conn, cursor):
                cursor.execute(query, params or ())
                return cursor.lastrowid
        except mysql.connector.Error:
            return None

    def fetch_one(self, query, params=None):
        """Execute SELECT and return a single row (dict) or None if no rows / failure."""
        try:
            with self._cursor(dictionary=True) as (conn, cursor):
                cursor.execute(query, params or ())
                return cursor.fetchone()
        except mysql.connector.Error:
            return None

    def fetch_all(self, query, params=None):
        """Execute SELECT and return all rows (list of dicts) or None on failure."""
        try:
            with self._cursor(dictionary=True) as (conn, cursor):
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except mysql.connector.Error:
            return None


# Global DB access object used across the app.
db_manager = DBManager(DB_CONFIG)



def _flight_arrival_expr():
    """
    SQL expression for computing an effective arrival timestamp.
    If Flight.arrival_datetime exists -> use it, otherwise calculate:
    departure_date + departure_time + Route.duration minutes.
    """
    return "COALESCE(f.arrival_datetime, DATE_ADD(TIMESTAMP(f.departure_date, f.departure_time), INTERVAL r.duration MINUTE))"


def check_location_continuity(entity_id, entity_type, new_origin, check_time):
    """
    Enforces "append-only" location continuity for scheduling.

    Meaning:
    - An entity (aircraft / pilot / attendant) can only be scheduled at the END of its chain
      (i.e., after its latest non-cancelled assigned flight, including future flights).
    - The next scheduled flight must depart from the destination of that latest flight.
    - The next scheduled flight must depart at/after that latest flight's arrival time.
    - If the entity has no flights in its chain -> it is assumed to be located at TLV.
    """
    arrival_expr = _flight_arrival_expr()

    if entity_type == 'aircraft':
        # Get the most recent (latest-arriving) non-cancelled flight for this aircraft.
        query = f"""
            SELECT r.destination, {arrival_expr} AS arrival_dt
            FROM Flight f
            JOIN Route r ON f.route_id = r.route_id
            WHERE f.aircraft_id = %s
              AND f.flight_status != 'Cancelled'
            ORDER BY arrival_dt DESC
            LIMIT 1
        """
        last_flight = db_manager.fetch_one(query, (entity_id,))
        if not last_flight:
            # No flights -> default starting location is TLV.
            return new_origin == 'TLV'
        # Allowed only if departing from last destination AND after last arrival.
        return (new_origin == last_flight['destination']) and (check_time >= last_flight['arrival_dt'])

    if entity_type == 'pilot':
        # Get the most recent (latest-arriving) non-cancelled flight for this pilot.
        query = f"""
            SELECT r.destination, {arrival_expr} AS arrival_dt
            FROM Pilots_on_Flights pf
            JOIN Flight f ON pf.flight_id = f.flight_id
            JOIN Route r ON f.route_id = r.route_id
            WHERE pf.employee_id = %s
              AND f.flight_status != 'Cancelled'
            ORDER BY arrival_dt DESC
            LIMIT 1
        """
        last_flight = db_manager.fetch_one(query, (entity_id,))
        if not last_flight:
            return new_origin == 'TLV'
        return (new_origin == last_flight['destination']) and (check_time >= last_flight['arrival_dt'])

    if entity_type == 'attendant':
        # Get the most recent (latest-arriving) non-cancelled flight for this flight attendant.
        query = f"""
            SELECT r.destination, {arrival_expr} AS arrival_dt
            FROM Flight_Attendant_on_Flights af
            JOIN Flight f ON af.flight_id = f.flight_id
            JOIN Route r ON f.route_id = r.route_id
            WHERE af.employee_id = %s
              AND f.flight_status != 'Cancelled'
            ORDER BY arrival_dt DESC
            LIMIT 1
        """
        last_flight = db_manager.fetch_one(query, (entity_id,))
        if not last_flight:
            return new_origin == 'TLV'
        return (new_origin == last_flight['destination']) and (check_time >= last_flight['arrival_dt'])

    # Unknown entity type -> reject by default.
    return False


def update_statuses():
    """
    Keeps flight and booking statuses consistent with real time and seat occupancy.

    Runs 3 maintenance updates:
    1) Flight status: when departure time has passed -> mark Active/Full flights as Performed.
    2) Booking status: when a flight becomes Performed -> mark its Active bookings as Performed.
    3) Flight occupancy: recalculate whether each Active/Full flight should be Active or Full
       based on the number of reserved seats in Active bookings.
    """

    # 1) Flights: once departure datetime is in the past -> Performed (only for Active/Full flights).
    db_manager.execute_query("""
        UPDATE Flight
        SET flight_status = 'Performed'
        WHERE TIMESTAMP(departure_date, departure_time) <= NOW()
          AND flight_status IN ('Active', 'Full')
    """)

    # 2) Bookings: once the flight is Performed -> the booking becomes Performed (only if it was Active).
    db_manager.execute_query("""
        UPDATE Booking b
        JOIN Flight f ON b.flight_id = f.flight_id
        SET b.booking_status = 'Performed'
        WHERE f.flight_status = 'Performed'
          AND b.booking_status = 'Active'
    """)

    # 3) Flights: update Active/Full based on seat occupancy (do not touch Performed/Cancelled).
    db_manager.execute_query("""
        UPDATE Flight f
        JOIN (
            SELECT f.flight_id,
                   (SELECT COUNT(*) FROM Seat s WHERE s.aircraft_id = f.aircraft_id) as total_seats,
                   (SELECT COUNT(*) FROM Reserved_Seat rs
                    JOIN Booking b ON rs.booking_id = b.booking_id
                    WHERE b.flight_id = f.flight_id AND b.booking_status = 'Active') as occupied_seats
            FROM Flight f
            WHERE f.flight_status IN ('Active', 'Full')
        ) as calc ON f.flight_id = calc.flight_id
        SET f.flight_status = CASE
            WHEN calc.occupied_seats >= calc.total_seats THEN 'Full'
            ELSE 'Active'
        END
        WHERE f.flight_status IN ('Active', 'Full')
    """)


@app.before_request
def before_request():
    """
    Flask hook that runs before every request.

    - Calls update_statuses() so the UI always reflects up-to-date statuses.
    - Enables "permanent" sessions and sets the session lifetime to 30 minutes.
    """
    update_statuses()
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)


@app.route('/')
def index():
    """
    Home page: displays flights.

    Manager view:
    - Shows all flights (any status), ordered by latest first.

    Customer view:
    - Shows only future flights that are Active and have at least 1 available seat.

    Also loads distinct origins/destinations for the search filters on the page.
    """
    if session.get('role') == 'manager':
        # available_seats = total seats in the aircraft - seats reserved by Active bookings.
        query = """
            SELECT f.*, r.origin, r.destination, r.duration,
            (SELECT COUNT(*) FROM Seat s WHERE s.aircraft_id = f.aircraft_id) -
            (SELECT COUNT(*) FROM Reserved_Seat rs WHERE rs.booking_id IN (SELECT booking_id FROM Booking WHERE flight_id = f.flight_id AND booking_status = 'Active'))
            as available_seats
            FROM Flight f
            JOIN Route r ON f.route_id = r.route_id
            ORDER BY f.departure_date DESC, f.departure_time DESC
        """
        flights = db_manager.fetch_all(query)
    else:
        # Customers can only see bookable flights: future + Active + seats available.
        query = """
            SELECT f.*, r.origin, r.destination, r.duration,
            (SELECT COUNT(*) FROM Seat s WHERE s.aircraft_id = f.aircraft_id) -
            (SELECT COUNT(*) FROM Reserved_Seat rs WHERE rs.booking_id IN (SELECT booking_id FROM Booking WHERE flight_id = f.flight_id AND booking_status = 'Active'))
            as available_seats
            FROM Flight f
            JOIN Route r ON f.route_id = r.route_id
            WHERE f.departure_date >= %s AND f.flight_status = 'Active'
            HAVING available_seats > 0
            ORDER BY f.departure_date, f.departure_time
        """
        flights = db_manager.fetch_all(query, (date.today(),))

    # Ensure the template always receives a list.
    if not flights:
        flights = []

    # Used to populate search dropdowns.
    destinations = db_manager.fetch_all("SELECT DISTINCT destination FROM Route") or []
    origins = db_manager.fetch_all("SELECT DISTINCT origin FROM Route") or []
    origins = origins or []  # ONE LINE FIX
    destinations = destinations or []


    return render_template(
        'index.html',
        flights=flights,
        destinations=destinations,
        origins=origins,
        date_today=date.today()
    )


@app.route('/search', methods=['POST'])
def search_flights():
    """
    Search endpoint for filtering flights.

    Inputs (from form):
    - origin, destination, date_from
    - status (only for managers)

    Behavior:
    - Manager: can filter by origin/destination/date/status across all flights.
    - Customer: can filter only Active flights, and always requires available seats > 0.
    """
    origin = request.form.get('origin')
    destination = request.form.get('destination')
    date_from = request.form.get('date_from')
    status_filter = request.form.get('status')

    # Query parameters are built dynamically based on which filters were provided.
    params = []

    if session.get('role') == 'manager':
        query = """
            SELECT f.*, r.origin, r.destination, r.duration,
            (SELECT COUNT(*) FROM Seat s WHERE s.aircraft_id = f.aircraft_id) -
            (SELECT COUNT(*) FROM Reserved_Seat rs WHERE rs.booking_id IN (SELECT booking_id FROM Booking WHERE flight_id = f.flight_id AND booking_status = 'Active'))
            as available_seats
            FROM Flight f
            JOIN Route r ON f.route_id = r.route_id
            WHERE 1=1
        """
    else:
        query = """
            SELECT f.*, r.origin, r.destination, r.duration,
            (SELECT COUNT(*) FROM Seat s WHERE s.aircraft_id = f.aircraft_id) -
            (SELECT COUNT(*) FROM Reserved_Seat rs WHERE rs.booking_id IN (SELECT booking_id FROM Booking WHERE flight_id = f.flight_id AND booking_status = 'Active'))
            as available_seats
            FROM Flight f
            JOIN Route r ON f.route_id = r.route_id
            WHERE f.flight_status = 'Active'
        """

    # Optional filters (added only if provided).
    if origin:
        query += " AND r.origin = %s"
        params.append(origin)
    if destination:
        query += " AND r.destination = %s"
        params.append(destination)
    if date_from:
        query += " AND f.departure_date = %s"
        params.append(date_from)
    elif session.get('role') != 'manager':
        # Customers default to showing from today forward if no date selected.
        query += " AND f.departure_date >= %s"
        params.append(date.today())

    # Managers can filter by status; customers cannot.
    if session.get('role') == 'manager' and status_filter:
        query += " AND f.flight_status = %s"
        params.append(status_filter)

    # Customers must have at least one available seat.
    if session.get('role') != 'manager':
        query += " HAVING available_seats > 0"

    query += " ORDER BY f.departure_date, f.departure_time"

    flights = db_manager.fetch_all(query, tuple(params))

    # Reload dropdown values for the page.
    destinations = db_manager.fetch_all("SELECT DISTINCT destination FROM Route")
    origins = db_manager.fetch_all("SELECT DISTINCT origin FROM Route")

    return render_template(
        'index.html',
        flights=flights,
        destinations=destinations,
        origins=origins,
        date_today=date.today()
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login handler.

    - GET: renders the login page.
    - POST: authenticates either a registered customer (by email+password)
      or a manager (by employee_id+password).
    On success, stores minimal identity info in the session and redirects home.
    """
    if request.method == 'POST':
        # Form inputs
        email = request.form.get('email')
        password = request.form.get('password')

        # Try customer login first (Registered_Customer table).
        user = db_manager.fetch_one(
            "SELECT * FROM Registered_Customer WHERE email = %s AND password = %s",
            (email, password)
        )

        if user:
            # Session identity for a logged-in customer.
            session['user_id'] = user['email']      # Primary user identifier (email)
            session['role'] = 'customer'            # Used for permissions / UI behavior
            session['name'] = user['email']         # Display name (currently email)
            return redirect(url_for('index'))

        # If not a customer, try manager login (Manager table).
        manager = db_manager.fetch_one(
            "SELECT * FROM Manager WHERE employee_id = %s AND password = %s",
            (email, password)
        )
        if manager:
            # Session identity for a logged-in manager.
            session['user_id'] = manager['employee_id']   # Primary user identifier (employee id)
            session['role'] = 'manager'                   # Used for permissions / UI behavior
            session['name'] = manager['first_name']       # Display name for the navbar/UI
            return redirect(url_for('index'))

        # Login failed.
        flash('פרטי התחברות שגויים', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Customer registration handler.

    - GET: renders registration form.
    - POST: validates input, ensures a Customer exists, then inserts a new Registered_Customer.
      Also stores multiple phone numbers in Customer_Phone (ignores duplicates).
    """
    if request.method == 'POST':
        # Required registration fields
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        passport = request.form['passport']
        birth_date = request.form['birth_date']
        password = request.form['password']

        # Allows multiple phone inputs from the form.
        phones = request.form.getlist('phones')

        # Validate: phone numbers must be digits only.
        for phone in phones:
            if phone.strip() and not phone.strip().isdigit():
                flash('מספר הטלפון חייב להכיל ספרות בלבד', 'danger')
                return render_template('register.html')

        try:
            # Ensure a base Customer record exists (Customer table).
            existing = db_manager.fetch_one("SELECT email FROM Customer WHERE email = %s", (email,))
            if not existing:
                db_manager.execute_query(
                    "INSERT INTO Customer (email, first_name, last_name) VALUES (%s, %s, %s)",
                    (email, first_name, last_name)
                )

            # Prevent duplicate registration in Registered_Customer.
            is_registered = db_manager.fetch_one(
                "SELECT email FROM Registered_Customer WHERE email = %s",
                (email,)
            )
            if is_registered:
                flash('המייל הזה כבר רשום במערכת', 'danger')
                return redirect(url_for('login'))

            # Create a registered customer account.
            db_manager.execute_query(
                "INSERT INTO Registered_Customer (email, passport_num, birth_date, password, register_date) "
                "VALUES (%s, %s, %s, %s, %s)",
                (email, passport, birth_date, password, date.today())
            )

            # Save phone numbers (IGNORE prevents duplicate (email, phone) rows if constrained).
            for phone in phones:
                if phone.strip():
                    db_manager.execute_query(
                        "INSERT IGNORE INTO Customer_Phone (email, phone_num) VALUES (%s, %s)",
                        (email, phone.strip())
                    )

            flash('ההרשמה בוצעה בהצלחה! אנא התחבר.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            # Generic error handler (DB errors, etc.).
            flash(f'שגיאה: {e}', 'danger')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/logout')
def logout():
    """
    Logs the user out by clearing the session and returning to the home page.
    """
    session.clear()
    return redirect(url_for('index'))


@app.route('/book/<int:flight_id>', methods=['GET', 'POST'])
def book_flight(flight_id):
    """
    Seat selection page for a given flight.

    - Loads flight + route + aircraft details.
    - Loads all seats for the aircraft and marks seats reserved by Active bookings.
    - POST: collects selected seats, calculates total price by seat class,
      and stores a temporary booking payload in the session (booking_temp).
    """
    # Load flight details (including route and aircraft metadata).
    flight = db_manager.fetch_one("""
        SELECT f.*, r.origin, r.destination, r.duration AS route_duration, a.manufacturer, a.size
        FROM Flight f
        JOIN Route r ON f.route_id = r.route_id
        JOIN Aircraft a ON f.aircraft_id = a.aircraft_id
        WHERE f.flight_id = %s
    """, (flight_id,))

    # Invalid flight id -> go back home.
    if not flight:
        return redirect(url_for('index'))

    # All seats for the aircraft, ordered by class then seat position.
    all_seats = db_manager.fetch_all(
        "SELECT * FROM Seat WHERE aircraft_id = %s ORDER BY class DESC, row_num, col_num",
        (flight['aircraft_id'],)
    )

    # Seats currently reserved by Active bookings for this flight.
    reserved = db_manager.fetch_all("""
        SELECT rs.row_num, rs.col_num
        FROM Reserved_Seat rs
        JOIN Booking b ON rs.booking_id = b.booking_id
        WHERE b.flight_id = %s AND b.booking_status = 'Active'
    """, (flight_id,))

    # Quick lookup structure for the template to mark seats as unavailable.
    reserved_set = {(r['row_num'], r['col_num']) for r in (reserved or [])}

    if request.method == 'POST':
        # Seat ids encoded as "row-col-class" (e.g., "12-A-Economy").
        selected_seats = request.form.getlist('selected_seats')

        if not selected_seats:
            flash('אנא בחר מושב אחד לפחות.', 'danger')
            return redirect(request.url)

        # Pricing is based on seat class.
        total_price = 0
        seats_info = []  # Stored for the next step (summary/confirmation screen).
        for s in selected_seats:
            row, col, cls = s.split('-')
            price = flight['price_business'] if cls == 'Business' else flight['price_economy']
            total_price += float(price)
            seats_info.append({'row': row, 'col': col, 'seat_class': cls, 'price': price})

        # Temporary booking payload (used by booking_summary to actually create the Booking/Reserved_Seat rows).
        session['booking_temp'] = {
            'flight_id': flight_id,
            'seats_info': seats_info,
            'total_price': total_price
        }

        return redirect(url_for('booking_summary'))

    return render_template('book_flight.html', flight=flight, all_seats=all_seats, reserved_set=reserved_set)

@app.route('/booking_summary', methods=['GET', 'POST'])
def booking_summary():
    """
    Booking confirmation step.

    Uses the temporary booking payload stored in session['booking_temp'] (selected seats + total price).
    - GET: shows a summary page before confirming.
    - POST: creates the Booking row + Reserved_Seat rows, then clears the temp session data.
      Supports both logged-in customers and guest bookings.
    """
    # Temporary booking data from the seat selection step.
    data = session.get('booking_temp')
    if not data:
        # If user refreshes / enters directly without selecting seats first.
        return redirect(url_for('index'))

    # Load flight details for display and for aircraft_id when reserving seats.
    flight = db_manager.fetch_one("""
        SELECT f.*, r.origin, r.destination, r.duration AS route_duration, a.manufacturer, a.size
        FROM Flight f
        JOIN Route r ON f.route_id = r.route_id
        JOIN Aircraft a ON f.aircraft_id = a.aircraft_id
        WHERE f.flight_id = %s
    """, (data['flight_id'],))

    if not flight:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Customer identity collection:
        # - If logged in: take email from session.
        # - If guest: require email + first/last name + at least one phone, and create customer records if needed.
        if session.get('user_id'):
            email = session['user_id']              # Logged-in customer email (user_id is email for customers)
            first_name = session.get('name') or ''  # Not strictly required for DB here, used for UI/consistency
            last_name = ''
            phones = []
        else:
            email = request.form.get('email', '').strip()
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            phones = [p.strip() for p in request.form.getlist('phones') if p.strip()]

            # Guest validation
            if not email or not first_name or not last_name:
                flash("נא למלא אימייל + שם פרטי + שם משפחה.", "danger")
                return redirect(url_for('booking_summary'))

            if len(phones) < 1:
                flash("חובה להזין לפחות מספר טלפון אחד.", "danger")
                return redirect(url_for('booking_summary'))

            # Ensure Customer exists for the guest (base customer record).
            existing_cust = db_manager.fetch_one("SELECT * FROM Customer WHERE email=%s", (email,))
            if not existing_cust:
                db_manager.execute_query(
                    "INSERT INTO Customer (email, first_name, last_name) VALUES (%s, %s, %s)",
                    (email, first_name, last_name)
                )

            # Store guest phone numbers (ignore duplicates).
            for p in phones:
                db_manager.execute_query(
                    "INSERT IGNORE INTO Customer_Phone (email, phone_num) VALUES (%s, %s)",
                    (email, p)
                )

        # Generate a human-friendly booking identifier.
        booking_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        # Create the booking (starts as Active).
        db_manager.execute_query("""
            INSERT INTO Booking (booking_id, email, flight_id, total_price, booking_status)
            VALUES (%s, %s, %s, %s, 'Active')
        """, (booking_id, email, data['flight_id'], data['total_price']))

        # Reserve each selected seat for this booking.
        for seat in data['seats_info']:
            db_manager.execute_query("""
                INSERT INTO Reserved_Seat (booking_id, aircraft_id, row_num, col_num)
                VALUES (%s, %s, %s, %s)
            """, (booking_id, flight['aircraft_id'], seat['row'], seat['col']))

        # Clear the temp data so it cannot be submitted twice.
        session.pop('booking_temp', None)

        flash(f'ההזמנה אושרה! מספר ההזמנה שלך הוא: {booking_id}', 'success')

        # After booking:
        # - Logged-in customer -> go to booking history.
        # - Guest / manager -> go back to home.
        if session.get('role') == 'customer':
            return redirect(url_for('my_bookings'))
        return redirect(url_for('index'))

    # GET: show confirmation page.
    return render_template('booking_summary.html', flight=flight, data=data)


@app.route('/my_bookings')
def my_bookings():
    """
    Customer booking history page.

    - Requires login.
    - Supports an optional status filter via query string (?status=Active/Performed/...).
    - Returns bookings with route info and a readable seats list (GROUP_CONCAT).
    """
    if not session.get('user_id'):
        return redirect(url_for('login'))

    user_email = session['user_id']  # Customer identifier (email)
    status_filter = request.args.get('status', 'All')

    # Booking list + flight/route metadata + aggregated seat list per booking.
    query = """
        SELECT b.*,
               f.departure_date, f.departure_time,
               r.origin, r.destination,
               COALESCE(sl.seats_list, '') AS seats_list
        FROM Booking b
        JOIN Flight f ON b.flight_id = f.flight_id
        JOIN Route r ON f.route_id = r.route_id
        LEFT JOIN (
            SELECT rs.booking_id,
                   GROUP_CONCAT(
                       CONCAT(rs.row_num, rs.col_num, ' (', s.class, ')')
                       ORDER BY rs.row_num, rs.col_num
                       SEPARATOR ', '
                   ) AS seats_list
            FROM Reserved_Seat rs
            JOIN Seat s
              ON s.aircraft_id = rs.aircraft_id
             AND s.row_num = rs.row_num
             AND s.col_num = rs.col_num
            GROUP BY rs.booking_id
        ) sl ON sl.booking_id = b.booking_id
        WHERE b.email = %s
    """
    params = [user_email]

    # Optional filtering by booking status.
    if status_filter != 'All':
        query += " AND b.booking_status = %s"
        params.append(status_filter)

    query += " ORDER BY b.booking_datetime DESC"

    bookings = db_manager.fetch_all(query, tuple(params))

    # Status values used by the UI filter dropdown.
    statuses = ['Active', 'Performed', 'Cancelled by Customer', 'Cancelled by System']

    return render_template(
        'my_bookings.html',
        bookings=bookings,
        statuses=statuses,
        current_filter=status_filter
    )

@app.route('/cancel_booking/<booking_id>')
def cancel_booking(booking_id):
    """
    Cancels an existing booking (customer-initiated).

    Rules:
    - Only the booking owner can cancel (logged-in check).
    - Cancellation is blocked if the flight departs in less than 36 hours.
    - If cancellation is allowed: reserved seats are released and the booking is marked
      as "Cancelled by Customer" with a 5% cancellation fee.
    """
    # Fetch booking with its flight date/time and route for validation and display.
    booking = db_manager.fetch_one("""
        SELECT b.*, f.departure_date, f.departure_time, r.origin, r.destination
        FROM Booking b
        JOIN Flight f ON b.flight_id = f.flight_id
        JOIN Route r ON f.route_id = r.route_id
        WHERE b.booking_id = %s
    """, (booking_id,))

    if not booking:
        return redirect(url_for('index'))

    # Security: a logged-in user can only cancel their own bookings.
    if session.get('user_id') and session['user_id'] != booking['email']:
        return redirect(url_for('my_bookings'))

    # Build a full departure datetime to compute the remaining time until departure.
    departure_dt = datetime.combine(booking['departure_date'], (datetime.min + booking['departure_time']).time())
    time_diff = departure_dt - datetime.now()

    # Cancellation policy: disallow cancellation within 36 hours of departure.
    if time_diff < timedelta(hours=36):
        flash("לא ניתן לבטל פחות מ-36 שעות לפני הטיסה.", "danger")

        # Logged-in customers go back to booking history (or referring page).
        if session.get('user_id'):
            return redirect(request.referrer or url_for('my_bookings'))

        # Guests see the booking dashboard with their current seats.
        seats_query = """
            SELECT rs.row_num, rs.col_num, s.class
            FROM Reserved_Seat rs
            JOIN Seat s ON rs.aircraft_id = s.aircraft_id
            AND rs.row_num = s.row_num
            AND rs.col_num = s.col_num
            WHERE rs.booking_id = %s
            ORDER BY rs.row_num, rs.col_num
        """
        seats = db_manager.fetch_all(seats_query, (booking_id,))
        return render_template('booking_dashboard.html', booking=booking, seats=seats)

    # Calculate cancellation fee (5% of the original booking price).
    original_price = float(booking['total_price'])
    cancellation_fee = original_price * 0.05

    # Release all reserved seats for this booking (free them for other customers).
    db_manager.execute_query("DELETE FROM Reserved_Seat WHERE booking_id = %s", (booking_id,))

    # Update booking status and price (fee remains as the charged amount).
    db_manager.execute_query("""
        UPDATE Booking
        SET booking_status = 'Cancelled by Customer',
            total_price = %s
        WHERE booking_id = %s
    """, (cancellation_fee, booking_id))

    flash(f"ההזמנה בוטלה. חויבת בדמי ביטול של 5% ({cancellation_fee:.2f}₪).", "info")

    # Redirect based on user type.
    if session.get('user_id'):
        return redirect(url_for('my_bookings'))
    else:
        # For guests, re-fetch the updated booking to reflect the new status/price in the UI.
        updated_booking = db_manager.fetch_one("""
            SELECT b.*, f.departure_date, f.departure_time, r.origin, r.destination
            FROM Booking b
            JOIN Flight f ON b.flight_id = f.flight_id
            JOIN Route r ON f.route_id = r.route_id
            WHERE b.booking_id = %s
        """, (booking_id,))
        return render_template('booking_dashboard.html', booking=updated_booking, seats=[])


@app.route('/manager/add_flight', methods=['GET', 'POST'])
def add_flight():
    """
    Multi-step flow for managers to create a new flight.

    Rules enforced:
    - Long flight (> 360 minutes): only Big aircraft + only qualified pilots/attendants.
    - Short flight (<= 360 minutes): any aircraft size (subject to overlap) + any pilots/attendants.
    - Time overlap checks prevent double-booking resources.
    - Location continuity checks prevent "teleporting" resources between airports.
    """
    if session.get('role') != 'manager':
        return redirect(url_for('index'))

    step = request.form.get('step', '1') if request.method == 'POST' else 1
    today = date.today().strftime('%Y-%m-%d')

    # Step 1: choose route + date/time
    if request.method == 'GET' or step == 1 or step == '1':
        routes = db_manager.fetch_all("SELECT * FROM Route")
        return render_template('manage_flights.html', step=1, routes=routes, min_date=today)

    # Step 2: check aircraft availability
    if step == 'check_availability':
        route_id = request.form.get('route_id')
        flight_date = request.form.get('date')
        flight_time = request.form.get('time')

        route = db_manager.fetch_one("SELECT origin, duration FROM Route WHERE route_id = %s", (route_id,))
        if not route:
            flash("שגיאה: מסלול לא נמצא", "error")
            return redirect(url_for('add_flight'))

        duration_minutes = int(route['duration'])
        flight_origin = route['origin']
        is_long_flight = duration_minutes > 360

        # Long flight -> only Big aircraft
        size_filter = " AND a.size = 'Big' " if is_long_flight else ""

        new_start_dt = datetime.strptime(f"{flight_date} {flight_time}", '%Y-%m-%d %H:%M')
        new_end_dt = new_start_dt + timedelta(minutes=duration_minutes)

        time_query = f"""
            SELECT a.* FROM Aircraft a
            WHERE 1=1
            {size_filter}
            AND a.aircraft_id NOT IN (
                SELECT f.aircraft_id FROM Flight f
                JOIN Route r ON f.route_id = r.route_id
                WHERE f.flight_status != 'Cancelled'
                AND (
                    TIMESTAMP(f.departure_date, f.departure_time) < %s
                    AND
                    ADDTIME(TIMESTAMP(f.departure_date, f.departure_time), SEC_TO_TIME(r.duration * 60)) > %s
                )
            )
        """

        all_time_available_aircrafts = db_manager.fetch_all(time_query, (new_end_dt, new_start_dt))

        # Enforce location continuity for aircraft
        final_aircrafts = []
        if all_time_available_aircrafts:
            for a in all_time_available_aircrafts:
                if check_location_continuity(a['aircraft_id'], 'aircraft', flight_origin, new_start_dt):
                    final_aircrafts.append(a)

        return render_template(
            'manage_flights.html',
            step=2,
            aircrafts=final_aircrafts,
            route_id=route_id,
            date=flight_date,
            time=flight_time
        )

    # Step 3: assign crew
    if step == 'assign_crew':
        route_id = request.form.get('route_id')
        flight_date = request.form.get('date')
        flight_time = request.form.get('time')
        aircraft_id = request.form.get('aircraft_id')

        if not all([route_id, flight_date, flight_time, aircraft_id]):
            flash("שגיאה: נתונים חסרים, אנא התחל מחדש", "error")
            return redirect(url_for('add_flight'))

        aircraft = db_manager.fetch_one("SELECT * FROM Aircraft WHERE aircraft_id = %s", (aircraft_id,))
        if not aircraft:
            flash("שגיאה: מטוס לא נמצא", "error")
            return redirect(url_for('add_flight'))

        route = db_manager.fetch_one("SELECT origin, duration FROM Route WHERE route_id = %s", (route_id,))
        if not route:
            flash("שגיאה: מסלול לא נמצא", "error")
            return redirect(url_for('add_flight'))

        duration_minutes = int(route['duration'])
        flight_origin = route['origin']
        is_long_flight = duration_minutes > 360

        # Long flight -> Big aircraft only (extra safety in case someone bypassed step 2)
        if is_long_flight and aircraft.get('size') != 'Big':
            flash("שגיאה: טיסה ארוכה דורשת מטוס גדול (Big).", "error")
            return redirect(url_for('add_flight'))

        # Crew requirement depends on aircraft size (your existing logic)
        req_pilots = 3 if aircraft['size'] == 'Big' else 2
        req_attendants = 6 if aircraft['size'] == 'Big' else 3

        new_start_dt = datetime.strptime(f"{flight_date} {flight_time}", '%Y-%m-%d %H:%M')
        new_end_dt = new_start_dt + timedelta(minutes=duration_minutes)

        # Qualification filter:
        # - Long flight: only qualified crew
        # - Short flight: everyone
        pilot_qual_filter = "AND p.is_qualified = 1" if is_long_flight else ""
        attendant_qual_filter = "AND a.is_qualified = 1" if is_long_flight else ""

        pilots_time_query = f"""
            SELECT p.*
            FROM Pilot p
            WHERE 1=1
              {pilot_qual_filter}
              AND p.employee_id NOT IN (
                  SELECT pf.employee_id
                  FROM Pilots_on_Flights pf
                  JOIN Flight f ON pf.flight_id = f.flight_id
                  JOIN Route r ON f.route_id = r.route_id
                  WHERE f.flight_status != 'Cancelled'
                    AND (
                        TIMESTAMP(f.departure_date, f.departure_time) < %s
                        AND COALESCE(f.arrival_datetime,
                            DATE_ADD(TIMESTAMP(f.departure_date, f.departure_time), INTERVAL r.duration MINUTE)
                        ) > %s
                    )
              )
        """

        attendants_time_query = f"""
            SELECT a.*
            FROM Flight_Attendant a
            WHERE 1=1
              {attendant_qual_filter}
              AND a.employee_id NOT IN (
                  SELECT af.employee_id
                  FROM Flight_Attendant_on_Flights af
                  JOIN Flight f ON af.flight_id = f.flight_id
                  JOIN Route r ON f.route_id = r.route_id
                  WHERE f.flight_status != 'Cancelled'
                    AND (
                        TIMESTAMP(f.departure_date, f.departure_time) < %s
                        AND COALESCE(f.arrival_datetime,
                            DATE_ADD(TIMESTAMP(f.departure_date, f.departure_time), INTERVAL r.duration MINUTE)
                        ) > %s
                    )
              )
        """

        pilots_time_ok = db_manager.fetch_all(pilots_time_query, (new_end_dt, new_start_dt))
        attendants_time_ok = db_manager.fetch_all(attendants_time_query, (new_end_dt, new_start_dt))

        # Enforce location continuity for crew
        final_pilots = []
        if pilots_time_ok:
            for p in pilots_time_ok:
                if check_location_continuity(p['employee_id'], 'pilot', flight_origin, new_start_dt):
                    final_pilots.append(p)

        final_attendants = []
        if attendants_time_ok:
            for a in attendants_time_ok:
                if check_location_continuity(a['employee_id'], 'attendant', flight_origin, new_start_dt):
                    final_attendants.append(a)

        # Warn if not enough crew is available
        if len(final_pilots) < req_pilots or len(final_attendants) < req_attendants:
            flash("אין מספיק אנשי צוות זמינים לטיסה שנבחרה.", "warning")

        return render_template(
            'manage_flights.html',
            step=3,
            aircraft=aircraft,
            pilots=final_pilots,
            attendants=final_attendants,
            req_pilots=req_pilots,
            req_attendants=req_attendants,
            route_id=route_id,
            date=flight_date,
            time=flight_time
        )

    # Step 4: create flight + assignments
    if step == 'create':
        try:
            route_id = request.form.get('route_id')
            flight_date = request.form.get('date')
            flight_time = request.form.get('time')
            aircraft_id = request.form.get('aircraft_id')
            price_eco = request.form.get('price_eco')
            price_bus = request.form.get('price_bus', 0)

            selected_pilots = request.form.getlist('pilots')
            selected_attendants = request.form.getlist('attendants')

            if not all([route_id, flight_date, flight_time, aircraft_id, price_eco]):
                flash("שגיאה: נתונים חסרים ביצירת טיסה", "error")
                return redirect(url_for('add_flight'))

            aircraft = db_manager.fetch_one("SELECT * FROM Aircraft WHERE aircraft_id = %s", (aircraft_id,))
            route = db_manager.fetch_one("SELECT origin, duration FROM Route WHERE route_id = %s", (route_id,))
            if not aircraft or not route:
                flash("שגיאה: נתוני מטוס/מסלול לא תקינים", "error")
                return redirect(url_for('add_flight'))

            duration_minutes = int(route['duration'])
            is_long_flight = duration_minutes > 360

            # Long flight -> Big aircraft only (extra safety)
            if is_long_flight and aircraft.get('size') != 'Big':
                flash("שגיאה: טיסה ארוכה דורשת מטוס גדול (Big).", "error")
                return redirect(url_for('add_flight'))

            req_pilots = 3 if aircraft['size'] == 'Big' else 2
            req_attendants = 6 if aircraft['size'] == 'Big' else 3

            if len(selected_pilots) != req_pilots or len(selected_attendants) != req_attendants:
                flash(f"שגיאה: מספר אנשי הצוות לא תואם. נדרש: {req_pilots} טייסים ו-{req_attendants} דיילים.", "error")
                return redirect(url_for('add_flight'))

            # Long flight -> crew must be qualified (extra safety)
            if is_long_flight:
                q_p = db_manager.fetch_one(
                    f"SELECT COUNT(*) AS cnt FROM Pilot WHERE employee_id IN ({','.join(['%s'] * len(selected_pilots))}) AND is_qualified = 1",
                    tuple(selected_pilots)
                )
                q_a = db_manager.fetch_one(
                    f"SELECT COUNT(*) AS cnt FROM Flight_Attendant WHERE employee_id IN ({','.join(['%s'] * len(selected_attendants))}) AND is_qualified = 1",
                    tuple(selected_attendants)
                )
                if (q_p and q_p.get('cnt', 0) != len(selected_pilots)) or (q_a and q_a.get('cnt', 0) != len(selected_attendants)):
                    flash("שגיאה: בטיסה ארוכה חובה לבחור אנשי צוות בעלי הכשרה.", "error")
                    return redirect(url_for('add_flight'))

            new_start_dt = datetime.strptime(f"{flight_date} {flight_time}", '%Y-%m-%d %H:%M')
            new_end_dt = new_start_dt + timedelta(minutes=duration_minutes)

            new_flight_id = db_manager.execute_query("""
                INSERT INTO Flight (route_id, aircraft_id, departure_date, departure_time, arrival_datetime, flight_status, price_economy, price_business)
                VALUES (%s, %s, %s, %s, %s, 'Active', %s, %s)
            """, (route_id, aircraft_id, flight_date, flight_time, new_end_dt, price_eco, price_bus))

            if not new_flight_id:
                flash("שגיאה: לא נוצר flight_id לטיסה החדשה", "error")
                return redirect(url_for('add_flight'))

            for pid in selected_pilots:
                db_manager.execute_query(
                    "INSERT INTO Pilots_on_Flights (flight_id, employee_id) VALUES (%s, %s)",
                    (new_flight_id, pid)
                )

            for aid in selected_attendants:
                db_manager.execute_query(
                    "INSERT INTO Flight_Attendant_on_Flights (flight_id, employee_id) VALUES (%s, %s)",
                    (new_flight_id, aid)
                )

            flash("הטיסה נוצרה בהצלחה!", "success")
            return redirect(url_for('index'))

        except Exception as e:
            flash(f"שגיאה ביצירת הטיסה: {str(e)}", "error")
            return redirect(url_for('add_flight'))

    return redirect(url_for('add_flight'))



@app.route('/manager/add_aircraft', methods=['GET', 'POST'])
def add_aircraft():
    """
    Allows a manager to add a new aircraft to the system.

    The process includes:
    - Validating that the aircraft ID is unique.
    - Saving aircraft metadata (manufacturer, size, purchase date).
    - Automatically generating seat layout based on aircraft size
      (Business + Economy for Big aircraft, Economy only for Small).
    """
    # Access control: only managers can add aircraft
    if session.get('role') != 'manager':
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Aircraft basic details
        aircraft_id = request.form.get('aircraft_id')
        manufacturer = request.form.get('manufacturer')
        size = request.form.get('size')
        purchase_date = request.form.get('purchase_date')

        # Ensure aircraft ID is unique
        existing = db_manager.fetch_one(
            "SELECT aircraft_id FROM Aircraft WHERE aircraft_id = %s",
            (aircraft_id,)
        )
        if existing:
            flash(f"שגיאה: מספר מטוס {aircraft_id} כבר קיים במערכת", "error")
            return redirect(url_for('add_aircraft'))

        # Economy seat configuration
        eco_rows_count = int(request.form.get('eco_rows'))
        eco_cols_count = int(request.form.get('eco_cols'))

        # Insert aircraft record
        db_manager.execute_query(
            "INSERT INTO Aircraft (aircraft_id, manufacturer, size, purchase_date) VALUES (%s, %s, %s, %s)",
            (aircraft_id, manufacturer, size, purchase_date)
        )

        # Track current row number for seat creation
        current_row = 1

        try:
            # Big aircraft have Business class seats first
            if size == 'Big':
                bus_rows_count = int(request.form.get('bus_rows'))
                bus_cols_count = int(request.form.get('bus_cols'))

                for r in range(1, bus_rows_count + 1):
                    for c in range(bus_cols_count):
                        col_letter = chr(65 + c)  # Convert 0 -> 'A', 1 -> 'B', etc.
                        db_manager.execute_query(
                            "INSERT INTO Seat (aircraft_id, row_num, col_num, class) VALUES (%s, %s, %s, 'Business')",
                            (aircraft_id, r, col_letter)
                        )
                current_row = bus_rows_count + 1

            # Create Economy seats
            for r in range(current_row, current_row + eco_rows_count):
                for c in range(eco_cols_count):
                    col_letter = chr(65 + c)
                    db_manager.execute_query(
                        "INSERT INTO Seat (aircraft_id, row_num, col_num, class) VALUES (%s, %s, %s, 'Economy')",
                        (aircraft_id, r, col_letter)
                    )

            flash("המטוס והמושבים נוספו בהצלחה", "success")
            return redirect(url_for('index'))

        except Exception as e:
            # Rollback is implicit per query; show error to manager
            flash(f"שגיאה בהוספת מושבים: {e}", "error")
            return redirect(url_for('add_aircraft'))

    # Initial GET request: show aircraft creation form
    return render_template('add_aircraft.html')


@app.route('/manager/add_employee', methods=['GET', 'POST'])
def add_employee():
    """
    Allows a manager to add a new employee to the system.

    Supported roles:
    - Manager
    - Pilot
    - Flight Attendant

    Includes:
    - Input validation
    - Hebrew-only name validation
    - Phone number validation
    - Qualification flag for long flights (pilots / attendants)
    """
    # Access control: only managers can add employees
    if session.get('role') != 'manager':
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Common employee fields
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        emp_id = request.form.get('employee_id')
        phone = request.form.get('phone')
        start_date = request.form.get('start_date')
        password = request.form.get('password')
        city = request.form.get('city')
        street = request.form.get('street')
        house_num = request.form.get('house_num')

        # Qualification flag (used for long flights)
        is_qualified = request.form.get('is_qualified', '0')
        is_qualified = 1 if str(is_qualified) == '1' else 0

        # Basic required fields validation
        if not all([first_name, last_name, role, emp_id, phone, start_date, city, street, house_num]):
            flash('נא למלא את כל השדות', 'danger')
            return redirect(url_for('add_employee'))

        # Validate Hebrew-only names
        if not re.match(r'^[\u0590-\u05FF\s]+$', first_name) or not re.match(r'^[\u0590-\u05FF\s]+$', last_name):
            flash('שם פרטי ושם משפחה חייבים להיות בעברית בלבד', 'danger')
            return redirect(url_for('add_employee'))

        # Validate phone number (digits only)
        if not phone.isdigit():
            flash('מספר הטלפון חייב להכיל ספרות בלבד', 'danger')
            return redirect(url_for('add_employee'))

        # Ensure employee ID is unique across all employee tables
        exists_manager = db_manager.fetch_one("SELECT employee_id FROM Manager WHERE employee_id = %s", (emp_id,))
        exists_pilot = db_manager.fetch_one("SELECT employee_id FROM Pilot WHERE employee_id = %s", (emp_id,))
        exists_fa = db_manager.fetch_one("SELECT employee_id FROM Flight_Attendant WHERE employee_id = %s", (emp_id,))

        if exists_manager or exists_pilot or exists_fa:
            flash('תעודת זהות זו כבר קיימת במערכת כעובד', 'danger')
            return redirect(url_for('add_employee'))

        try:
            # Manager requires a password
            if role == 'manager':
                if not password:
                    flash('חובה להזין סיסמה למנהל', 'danger')
                    return redirect(url_for('add_employee'))

                db_manager.execute_query(
                    "INSERT INTO Manager (employee_id, first_name, last_name, employee_phone, start_date, city, street, house_num, password) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (emp_id, first_name, last_name, phone, start_date, city, street, house_num, password)
                )
            else:
                # Insert Pilot or Flight Attendant
                table = 'Pilot' if role == 'pilot' else 'Flight_Attendant'
                db_manager.execute_query(
                    f"INSERT INTO {table} (employee_id, first_name, last_name, employee_phone, start_date, city, street, house_num, is_qualified) "
                    f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (emp_id, first_name, last_name, phone, start_date, city, street, house_num, is_qualified)
                )

            flash('העובד נוסף בהצלחה', 'success')
        except Exception as e:
            flash(f'שגיאה בהוספת העובד: {e}', 'danger')

        return redirect(url_for('add_employee'))

    # Initial GET request: show employee creation form
    return render_template('add_employee.html')

@app.route('/cancel_flight/<int:flight_id>')
def cancel_flight(flight_id):
    """
    Allows a manager to cancel a flight, subject to business rules.

    Rules:
    - Only managers can cancel flights.
    - A flight can be cancelled only if departure is more than 72 hours away.
    - Cancelling a flight:
        * Marks the flight as 'Cancelled'
        * Cancels all active bookings by system
        * Resets booking price to 0
        * Frees all reserved seats
    """
    # Access control: only managers can cancel flights
    if session.get('role') != 'manager':
        return redirect(url_for('index'))

    # Fetch flight details
    flight = db_manager.fetch_one(
        "SELECT * FROM Flight WHERE flight_id = %s",
        (flight_id,)
    )
    if not flight:
        flash('טיסה לא נמצאה', 'danger')
        return redirect(url_for('index'))

    # Calculate time until departure
    flight_dt = datetime.combine(
        flight['departure_date'],
        (datetime.min + flight['departure_time']).time()
    )

    # Enforce 72-hour cancellation policy
    if flight_dt - datetime.now() < timedelta(hours=72):
        flash('לא ניתן לבטל טיסה פחות מ-72 שעות לפני ההמראה.', 'danger')
        return redirect(url_for('index'))

    # Cancel the flight
    db_manager.execute_query(
        "UPDATE Flight SET flight_status = 'Cancelled' WHERE flight_id = %s",
        (flight_id,)
    )

    # Cancel all active bookings related to this flight
    db_manager.execute_query("""
        UPDATE Booking
        SET booking_status = 'Cancelled by System',
            total_price = 0
        WHERE flight_id = %s AND booking_status = 'Active'
    """, (flight_id,))

    # Remove all reserved seats for the cancelled flight
    db_manager.execute_query("""
        DELETE rs FROM Reserved_Seat rs
        INNER JOIN Booking b ON rs.booking_id = b.booking_id
        WHERE b.flight_id = %s
    """, (flight_id,))

    flash('הטיסה בוטלה וכל ההזמנות בוטלו ללא חיוב.', 'success')
    return redirect(url_for('index'))


@app.route('/manager/reports')
def reports():
    """
    Displays management reports dashboard.

    Reports included:
    1. Monthly aircraft utilization and dominant route
    2. Monthly booking cancellation rate
    3. Revenue by aircraft size, manufacturer and seat class
    4. Average occupancy rate for performed flights
    """
    # Access control: only managers can view reports
    if session.get('role') != 'manager':
        return redirect(url_for('index'))

    # Report 1: Monthly summary per aircraft
    query1 = """
        SELECT
            Stats.aircraft_id,
            Stats.Month,
            Stats.Flights_Performed,
            Stats.Flights_Cancelled,
            ROUND((Stats.performed_minutes / 60.0) / (30 * 24) * 100, 2) AS Utilization_Pct,
            (SELECT CONCAT(r.origin, '-', r.destination)
             FROM Flight as f
             JOIN Route as r ON f.route_id = r.route_id
             WHERE f.aircraft_id = Stats.aircraft_id
               AND DATE_FORMAT(f.departure_date, '%Y-%m') = Stats.Month
               AND f.flight_status = 'Performed'
             GROUP BY r.origin, r.destination
             ORDER BY COUNT(*) DESC
             LIMIT 1) AS Dominant_Route
        FROM (
            SELECT
                f.aircraft_id,
                DATE_FORMAT(f.departure_date, '%Y-%m') AS Month,
                SUM(CASE WHEN f.flight_status = 'Performed' THEN 1 ELSE 0 END) AS Flights_Performed,
                SUM(CASE WHEN f.flight_status LIKE 'Cancel%' THEN 1 ELSE 0 END) AS Flights_Cancelled,
                COALESCE(SUM(CASE WHEN f.flight_status = 'Performed' THEN r.duration ELSE 0 END), 0) AS performed_minutes
            FROM Flight as f
            JOIN Route as r ON f.route_id = r.route_id
            WHERE f.departure_date <= CURRENT_DATE()
            GROUP BY f.aircraft_id, DATE_FORMAT(f.departure_date, '%Y-%m')
        ) Stats
        ORDER BY Stats.Month DESC, Stats.aircraft_id
    """
    report1_data = db_manager.fetch_all(query1) or []

    # Report 2: Monthly booking cancellation rate
    query2 = """
        SELECT
            DATE_FORMAT(booking_datetime, '%Y-%m') AS Booking_Month,
            COUNT(*) AS Total_Bookings,
            SUM(CASE WHEN booking_status LIKE 'Cancel%' THEN 1 ELSE 0 END) AS Cancelled_Count,
            ROUND(
                (SUM(CASE WHEN booking_status LIKE 'Cancel%' THEN 1 ELSE 0 END) / COUNT(*)) * 100,
                2
            ) AS Cancellation_Rate
        FROM Booking
        GROUP BY DATE_FORMAT(booking_datetime, '%Y-%m')
        ORDER BY Booking_Month DESC
    """
    report2_data = db_manager.fetch_all(query2) or []

    # Report 3: Revenue by aircraft and seat class
    query3 = """
        SELECT
            A.size AS Size,
            A.manufacturer AS Manufacturer,
            S.class AS Class,
            COALESCE(SUM(
                CASE
                    WHEN S.class = 'Economy' THEN F.price_economy
                    WHEN S.class = 'Business' THEN F.price_business
                    ELSE 0
                END
            ), 0) AS Total_Revenue
        FROM Aircraft AS A
        JOIN Seat AS S ON A.aircraft_id = S.aircraft_id
        LEFT JOIN Reserved_Seat RS
               ON S.aircraft_id = RS.aircraft_id
              AND S.row_num = RS.row_num
              AND S.col_num = RS.col_num
        LEFT JOIN Booking AS B
               ON RS.booking_id = B.booking_id
              AND B.booking_status IN ('Active', 'Performed', 'Cancelled by Customer')
        LEFT JOIN Flight AS F ON B.flight_id = F.flight_id
        GROUP BY A.size, A.manufacturer, S.class
        ORDER BY Total_Revenue DESC
    """
    report3_data = db_manager.fetch_all(query3) or []

    # Report 4: Average occupancy rate for performed flights
    query4 = """
        SELECT AVG((occupied_seats * 100.0) / total_seats) AS average_occupancy
        FROM (
            SELECT
                f.flight_id,
                (SELECT COUNT(*)
                 FROM Seat AS s
                 WHERE s.aircraft_id = f.aircraft_id) AS total_seats,
                (SELECT COUNT(*)
                 FROM Reserved_Seat rs
                 JOIN Booking b ON rs.booking_id = b.booking_id
                 WHERE b.flight_id = f.flight_id
                   AND b.booking_status = 'Performed') AS occupied_seats
            FROM Flight f
            WHERE f.flight_status = 'Performed'
        ) AS calc_table
    """
    report4_row = db_manager.fetch_one(query4) or {}
    average_occupancy = report4_row.get('average_occupancy')

    return render_template(
        'reports.html',
        report1=report1_data,
        report2=report2_data,
        report3=report3_data,
        average_occupancy=average_occupancy
    )


@app.route('/manage_booking_guest', methods=['GET', 'POST'])
def manage_booking_guest():
    """
    Allows a non-registered (guest) customer to view an active booking.

    Identification is done using:
    - Booking ID
    - Email address

    Only active bookings can be retrieved.
    """
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        email = request.form.get('email')

        # Fetch active booking matching booking ID and email
        query = """
            SELECT b.*, f.departure_date, f.departure_time, r.origin, r.destination
            FROM Booking b
            JOIN Flight f ON b.flight_id = f.flight_id
            JOIN Route r ON f.route_id = r.route_id
            WHERE b.booking_id = %s
              AND b.email = %s
              AND b.booking_status = 'Active'
        """
        booking = db_manager.fetch_one(query, (booking_id, email))

        if booking:
            # Retrieve reserved seats for the booking
            seats_query = """
                SELECT rs.row_num, rs.col_num, s.class
                FROM Reserved_Seat rs
                JOIN Seat s
                  ON rs.aircraft_id = s.aircraft_id
                 AND rs.row_num = s.row_num
                 AND rs.col_num = s.col_num
                WHERE rs.booking_id = %s
                ORDER BY rs.row_num, rs.col_num
            """
            seats = db_manager.fetch_all(seats_query, (booking_id,))
            return render_template('booking_dashboard.html', booking=booking, seats=seats)
        else:
            flash('פרטי ההזמנה שגויים או לא נמצאו.', 'danger')

    # Initial GET request: show booking lookup form
    return render_template('manage_booking.html')



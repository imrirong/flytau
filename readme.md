# FLYTAU – Flight Management System

FLYTAU is a web-based flight management system developed as a final project.

## Technologies
- Python (developed using PyCharm)
- Flask
- MySQL
- HTML / CSS
- Git & GitHub
- PythonAnywhere

## System Description
The system simulates an airline management platform and supports:
- Flight creation, scheduling, and cancellation
- Seat selection and booking management
- Aircraft management 
- Pilot and flight attendant management
- Customer and guest bookings
- Manager dashboard and operational reports

## User Roles
- Customer – can view and book available flights
- Guest – can book flights and manage bookings without registration
- Manager – can manage flights, aircraft, employees, and view reports

## Project Structure and Usage
This repository contains the full source code of the FLYTAU system.

Main contents:
- `app.py` – Main Flask application file (routes, business logic, and database access)
- `templates/` – HTML templates for the user interface
- `static/` – Static files such as CSS
- `schema.sql` – Database schema and sample data
- `.env` – Environment variables for database configuration (not included in the repository)

## How to Use
The system is a web-based application.
Users interact with the system through a web browser.
Managers and customers access the system via the login page according to their role.



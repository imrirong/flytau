# FLYTAU – Flight Management System

FLYTAU is a web-based flight management system developed as a final project.

The system was written in **Python** using the **PyCharm IDE** and built with a Flask backend
connected to a MySQL database.

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
- Aircraft management with automatic seat generation
- Pilot and flight attendant management
- Customer and guest bookings
- Manager dashboard with operational reports

## User Roles
- Customer – can view and book available flights
- Guest – can book flights and manage bookings without registration
- Manager – can manage flights, aircraft, employees, and view reports

## Key Features
- Location continuity (append-only scheduling for aircraft and crew)
- Separation between short and long flights with qualification rules
- Automatic flight and booking status updates based on time and occupancy
- Role-based access control
- Custom 404 error page for improved user experience

## Deployment
The system is deployed on **PythonAnywhere** and connected to a remote **MySQL** database.
All data changes are stored persistently in the database.



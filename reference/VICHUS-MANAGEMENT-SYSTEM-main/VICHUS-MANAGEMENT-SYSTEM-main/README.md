# Vichu Management - Attendance Tracking System

A professional Employee Attendance Management System built with Django, featuring QR code-based punching, real-time status tracking, and automated work-hour calculations.

## 🚀 Features

- **User Profiles:** Specialized `EmployeeProfile` extending the base Django User model.
- **QR Code Punching:** Automatically generates unique QR codes for every employee for quick check-ins/check-outs.
- **Dynamic Status Tracking:** Support for various states:
    - `Working`, `Break`, `Out`
    - `Self Training`, `Research`, `Learning New Topics`, `In Meeting`, `Need Help`
- **Time Calculation:** Accurate accumulation of working seconds with real-time updates.
- **Compliance Check:** Visual cues or flags for employees who have completed at least 8 hours of work.
- **Audit Logs:** Comprehensive `PunchLog` capturing timestamps and IP addresses for every status change.
- **Management Console:** Admin dashboard for monitoring all employee statuses and attendance history.

## 🛠️ Tech Stack

- **Backend:** Django 5.x
- **Database:** SQLite (default, can be configured for PostgreSQL)
- **Image Handling:** Pillow (for QR codes and profile media)
- **QR Generation:** qrcode library
- **Styling:** Vanilla CSS (Modern, Premium Aesthetics)

## 📋 Installation & Setup

### 1. Prerequisites
- Python 3.10+
- Pip

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone <repository-url>
cd Vichu_Management

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Linux/Mac
```

### 3. Install Dependencies
```bash
pip install django pillow qrcode
```

### 4. Database Initialization
```bash
# Run migrations
python manage.py migrate

# Seed the database with initial users and management accounts
python seed_db.py
```

## 🏃 Running the Application

```bash
python manage.py runserver
```

Access the application at `http://127.0.0.1:8000/`.

## 👤 Initial Credentials
The `seed_db.py` script creates the following default accounts:

| Role | Username | Password | Notes |
|------|----------|----------|-------|
| **Admin** | `vismaya` | `vichu@123` | Full admin access |
| **Developer** | `dev001` to `dev100` | `pass123` | Tester accounts |

## 📁 Project Structure

- `attendance/`: Main application logic, models, and views.
- `employee_mgmt/`: Project configuration (settings, urls).
- `media/qrcodes/`: Generated QR codes for employees.
- `static/`: Custom CSS and Javascript files.
- `templates/`: HTML templates for the dashboard and login pages.

## 🛡️ License
This project is for internal management use. All rights reserved.

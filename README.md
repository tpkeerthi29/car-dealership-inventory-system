# Car Dealership Inventory System

Car Dealership Inventory System — TDD Kata assessment.

A full-stack application for managing vehicle inventory, searching vehicles, and handling purchases. It includes a FastAPI backend, a React/Vite frontend, SQLite persistence, authentication, and role-based access for administrators and regular users.

## Features

- User registration and login
- JWT-based authentication
- Separate administrator and regular-user experiences
- View and search vehicle inventory by make, model, and category
- Administrator actions: add, edit, delete, and restock vehicles
- Regular-user action: purchase available vehicle stock
- Stock quantity validation
- SQLite database
- Automated backend tests with pytest

## Technology Stack

### Backend
- Python 3.12
- FastAPI
- SQLAlchemy
- SQLite
- PyJWT
- pwdlib
- pytest

### Frontend
- React
- Vite
- Tailwind CSS

## Project Structure

```text
car-dealership-inventory-system/
├── backend/
│   ├── app/
│   └── tests/
├── frontend/
├── screenshots/
├── .gitignore
└── README.md
```

## Prerequisites

Install the following before running the project:

- Python 3.12
- Node.js and npm

## Run the Backend

Open a terminal in the project root, then run:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API should be available at:

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs

If PowerShell blocks virtual-environment activation, run the environment's Python executable directly instead:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Run the Frontend

Open a **second terminal** in the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in the terminal (commonly http://localhost:5173 or another available port).

Keep the backend and frontend terminals running while using the application.

## Run the Tests

From the project root, run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_vehicles.py -q
```

The test run completed with **22 passed** in the development environment before the final authentication-token change. Rerun the command after your final code changes and update this result if it changes.

## Authentication and Roles

- New registrations are assigned the regular-user role.
- Administrator accounts have elevated inventory-management permissions.
- The backend uses bearer tokens for authenticated API requests.
- Do not publish real passwords, secret keys, or production credentials in this repository.

An administrator account was configured locally for development. Account setup may need to be repeated when running the project with a fresh database.

## Assumptions and Limitations

- The application is intended as a local assessment/demo project, not a production deployment.
- SQLite is used for persistence; the database file is created locally and is excluded from Git.
- The frontend and backend are run separately during development.
- The configured CORS origins are local development origins.
- A fresh local database may require administrator-account setup before administrator features can be tested.
- Production deployment would require secure environment-based secret configuration, stronger operational controls, and deployment-specific CORS settings.

## Screenshots

The `screenshots/` directory contains screenshots documenting the application interface and development/testing evidence.

## AI Tool Usage

AI assistance was used during development for guidance with implementation, troubleshooting, and documentation. The generated suggestions were reviewed and tested during development, including running the backend test suite and manually checking application workflows. The developer remains responsible for understanding and explaining the submitted implementation.


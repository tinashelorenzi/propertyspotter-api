# Property Spotter API

A lead generation tool for property companies and agents.

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Project Structure

- `propertyspotter/` - Main project directory
- `api/` - API application
- `users/` - User management application
- `properties/` - Property management application
- `leads/` - Lead management application

## API Documentation

API documentation will be available at `/api/docs/` when the server is running. 
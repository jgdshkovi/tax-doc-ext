# Tax Automation

A full-stack web application for automating tax calculations and processing.

## Project Structure

- **`api/`** - Python Flask backend API
  - `app.py` - Main Flask application
  - `tac_calc.py` - Tax calculation logic
  - `schemas_.py` - Data schemas
  - `requirements.txt` - Python dependencies

- **`frontend/`** - React frontend application
  - `src/` - React components and application logic
  - `AdvancedUpload.js` - File upload functionality
  - `AdvancedResults.js` - Results display

## Quick Start

### Backend
```bash
cd api
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Features

- Tax calculation processing
- File upload capabilities
- Advanced results visualization
- REST API backend with React frontend

## Configuration

Nginx configuration files are included for production deployment.

# AI Tax Return Agent Prototype

An end-to-end prototype of an AI agent that automates personal tax return preparation by processing tax documents and generating completed Form 1040.

## Features

- **Document Upload**: Accepts W-2, 1099-INT, and 1099-NEC PDFs
- **Intelligent Parsing**: Extracts relevant tax data using OCR and document processing
- **Tax Calculation**: Applies 2024 IRS tax brackets and standard deductions
- **Form 1040 Generation**: Creates downloadable completed tax returns
- **Clean Interface**: Simple upload and results workflow

## Project Structure

- **`api/`** - Python Flask backend
  - `tac_calc.py` - Tax calculation logic and IRS tax brackets
  - `app.py` - Main API endpoints for upload and processing
  - `schemas_.py` - Document parsing and validation

- **`frontend/`** - React application
  - `AdvancedUpload.js` - Multi-file PDF upload interface
  - `AdvancedResults.js` - Tax summary and Form 1040 download

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

## Workflow

1. Upload tax documents (W-2, 1099s)
2. AI extracts and validates tax data
3. Calculates tax liability using current IRS rules
4. Generates completed Form 1040 for download

*Note: This is a prototype for demonstration purposes. Production use would require additional security, compliance, and IRS integration features.*

# FinTechCo 🛡️ Fraud Detection System

A comprehensive, real-time fraud detection system with machine learning capabilities, built with React, TypeScript, Flask, and Python.

## Overview
Real-time fraud detection system for monitoring financial transactions and identifying suspicious activities.

## Features
- Real-time transaction monitoring
- Risk scoring algorithm
- Dashboard for security analysts
- API for transaction validation

## Requirements
- Python 3.13+ (recommended)
- Node.js 18+ (for frontend)

## Quick Start
```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip3 install -r requirements.txt
python3 app.py

# Frontend
cd frontend
npm install
npm start
```

## Security Notes
- All financial amounts use Decimal type for precision
- PCI DSS compliant architecture
- Input validation on all endpoints
- Encrypted data transmission

## Demo Points
1. Codebase analysis and understanding
2. Adding real-time monitoring features
3. Security review and compliance checks
4. Automated testing and documentation

## Architecture
See `/docs/architecture.png` for system design.
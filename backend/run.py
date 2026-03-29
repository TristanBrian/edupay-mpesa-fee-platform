#!/usr/bin/env python3
"""
Entry point for running the EduPay API server.

Usage:
    cd backend
    python run.py
    
Or with uvicorn directly:
    cd backend
    uvicorn app.main:app --reload --port 8000
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

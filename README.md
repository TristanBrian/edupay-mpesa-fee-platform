# EduPay - Smart Student Finance Platform

A comprehensive platform enabling flexible school fee payments through M-Pesa, featuring installment plans, micro-loans, credit scoring, and advanced analytics for Kenyan schools.

## Overview

EduPay solves the challenge of school fee collection by providing:
- **Flexible Payment Options** - Let parents pay in installments instead of lump sums
- **Mobile-First Payments** - Seamless M-Pesa integration for easy payments
- **Micro-Loans** - Embedded finance to help parents bridge fee gaps
- **Smart Analytics** - Data-driven insights for school administrators

## Features

### Payment Management
| Feature | Description |
|---------|-------------|
| M-Pesa STK Push | One-click mobile payments via Safaricom M-Pesa |
| Payment Tracking | Real-time status updates and transaction history |
| Invoice Management | Create, track, and manage fee invoices per student |
| Automated Reminders | SMS/notification reminders for due payments |

### Flexible Payment Plans
| Feature | Description |
|---------|-------------|
| Installment Plans | Split fees into weekly, bi-weekly, or monthly payments |
| Custom Schedules | Flexible start dates and payment frequencies |
| Late Fee Management | Configurable penalties for overdue payments |
| Progress Tracking | Visual progress indicators for payment completion |

### Micro-Loans (Embedded Finance)
| Feature | Description |
|---------|-------------|
| Loan Applications | Simple application process for fee loans |
| Credit Scoring | Automated assessment based on payment history |
| Risk Assessment | ML-powered default probability prediction |
| Repayment Tracking | Amortization schedules with principal/interest breakdown |

### Analytics & Reporting
| Feature | Description |
|---------|-------------|
| Collection Metrics | Track rates, trends, and outstanding balances |
| Payment Patterns | Analyze timing distributions and behavior |
| Predictive Analytics | Forecast future collections |
| At-Risk Identification | Early warning system for potential defaults |

### Security
- Rate limiting and DDoS protection
- Input validation and SQL injection prevention
- Comprehensive audit logging
- Secure M-Pesa credential handling
- OWASP recommended security headers

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database**: SQLAlchemy with async support
- **Payments**: Safaricom M-Pesa Daraja API
- **Validation**: Pydantic v2

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Charts**: Recharts
- **State**: React Hooks + SWR

## Project Structure

```
edupay/
├── app/                          # Next.js frontend
│   ├── dashboard/
│   │   ├── page.tsx              # Dashboard overview
│   │   ├── students/             # Student management
│   │   ├── payments/             # Payment processing
│   │   ├── installments/         # Installment plans
│   │   ├── loans/                # Micro-loans
│   │   ├── analytics/            # Reports & analytics
│   │   └── settings/             # Configuration
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── ui/                       # Reusable UI components
│   ├── layout/                   # Sidebar, header
│   └── dashboard/                # Dashboard widgets
├── lib/
│   ├── api.ts                    # API client
│   └── utils.ts                  # Utilities
├── backend/
│   └── app/
│       ├── main.py               # FastAPI entry point
│       ├── config.py             # Configuration
│       ├── middleware.py         # Security middleware
│       ├── models/
│       │   ├── database.py       # DB connection
│       │   └── payment.py        # SQLAlchemy models
│       ├── routes/
│       │   ├── payments.py       # M-Pesa endpoints
│       │   ├── installments.py   # Installment plans
│       │   ├── loans.py          # Micro-loans
│       │   ├── analytics.py      # Reporting
│       │   └── ...               # Other routes
│       └── services/
│           ├── mpesa.py          # M-Pesa integration
│           ├── credit_scoring.py # Credit assessment
│           ├── analytics.py      # Analytics engine
│           └── security.py       # Security utilities
└── public/
    └── logo.jpg                  # EduPay logo
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Safaricom Developer Account (for M-Pesa)
- ngrok (for localhost callback testing)

### Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:3000
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your M-Pesa credentials

# Run server
uvicorn app.main:app --reload --port 8000

# API docs at http://localhost:8000/docs
```

## M-Pesa STK Push Testing Guide

### Step 1: Get Daraja API Credentials

1. Go to [Safaricom Developer Portal](https://developer.safaricom.co.ke)
2. Create an account and log in
3. Create a new app (select Lipa Na M-Pesa Sandbox)
4. Copy your **Consumer Key** and **Consumer Secret**

### Step 2: Setup ngrok for Callbacks

M-Pesa requires a publicly accessible callback URL. Use ngrok for localhost:

```bash
# Install ngrok (https://ngrok.com/download)

# Start ngrok tunnel to your backend
ngrok http 8000

# You'll see something like:
# Forwarding: https://a1b2c3d4.ngrok.io -> http://localhost:8000
```

### Step 3: Configure Environment

Update your `.env` file:

```env
# Your Daraja credentials
MPESA_CONSUMER_KEY=your_actual_consumer_key
MPESA_CONSUMER_SECRET=your_actual_consumer_secret

# Sandbox defaults (keep these for testing)
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919

# Your ngrok URL + callback path
MPESA_CALLBACK_URL=https://a1b2c3d4.ngrok.io/api/v1/payments/callback

# Switch to real API
MOCK_MPESA=false
```

### Step 4: Test STK Push

1. Start the backend: `uvicorn app.main:app --reload --port 8000`
2. Start the frontend: `npm run dev`
3. Go to Dashboard > Payments > New STK Push
4. Enter your Safaricom phone number and amount
5. Click "Send STK Push"
6. Check your phone for the M-Pesa prompt
7. Enter your PIN to complete payment

### Mock Mode Testing

For UI testing without real M-Pesa:

```env
MOCK_MPESA=true
```

Use the "Simulate Success" button in the payment dialog to test the full flow.

## API Reference

### Payments
```
POST   /api/v1/payments/initiate          # Initiate M-Pesa STK Push
POST   /api/v1/payments/callback          # M-Pesa callback handler
GET    /api/v1/payments/status/{id}       # Check payment status
GET    /api/v1/payments/                  # List all payments
```

### Installment Plans
```
POST   /api/v1/installments/plans                              # Create plan
GET    /api/v1/installments/plans                              # List plans
GET    /api/v1/installments/plans/{id}                         # Get plan details
GET    /api/v1/installments/plans/{id}/schedule                # Get schedule
POST   /api/v1/installments/plans/{id}/installments/{n}/pay    # Pay installment
```

### Loans
```
GET    /api/v1/loans/credit-score/{guardian_id}    # Get credit score
GET    /api/v1/loans/eligibility/{guardian_id}     # Check eligibility
POST   /api/v1/loans/apply                         # Apply for loan
POST   /api/v1/loans/{id}/approve                  # Approve/reject
POST   /api/v1/loans/{id}/disburse                 # Disburse funds
GET    /api/v1/loans/{id}/repayments               # Get repayment schedule
```

### Analytics
```
GET    /api/v1/analytics/collections/overview          # Collection metrics
GET    /api/v1/analytics/collections/trends            # Payment trends
GET    /api/v1/analytics/patterns/analysis             # Pattern analysis
GET    /api/v1/analytics/predictions/collections       # Forecasts
GET    /api/v1/analytics/predictions/at-risk-students  # At-risk alerts
GET    /api/v1/analytics/dashboard/summary             # Dashboard data
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MPESA_CONSUMER_KEY` | Safaricom API consumer key | Yes |
| `MPESA_CONSUMER_SECRET` | Safaricom API consumer secret | Yes |
| `MPESA_SHORTCODE` | Business shortcode | Yes |
| `MPESA_PASSKEY` | Online passkey | Yes |
| `MPESA_CALLBACK_URL` | Payment notification URL | Yes |
| `DATABASE_URL` | Database connection string | Yes |
| `ENVIRONMENT` | `sandbox` or `production` | No |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend | No |

## Credit Scoring Model

The credit scoring system evaluates loan eligibility based on:

| Component | Weight | Factors |
|-----------|--------|---------|
| Payment History | 35% | On-time vs late vs missed payments |
| Credit Utilization | 30% | Outstanding balance ratio |
| History Length | 15% | Duration of payment relationship |
| Consistency | 20% | Payment regularity and patterns |

**Score Range**: 300-850

| Risk Level | Score Range | Loan Terms |
|------------|-------------|------------|
| Low Risk | 700+ | Best rates, longest tenure |
| Medium Risk | 550-699 | Standard terms |
| High Risk | 400-549 | Higher rates, shorter tenure |
| Very High Risk | <400 | Not eligible |

## Security Best Practices

1. **Never commit `.env`** - Contains sensitive M-Pesa credentials
2. **Use HTTPS** - All production traffic must be encrypted
3. **Validate callbacks** - Verify M-Pesa callback signatures
4. **Monitor logs** - Review audit logs for suspicious activity
5. **Rotate credentials** - Change API keys periodically

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please open a GitHub issue or contact support@edupay.co.ke

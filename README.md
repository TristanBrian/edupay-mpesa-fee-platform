# FlexiFees - Smart Student Finance Platform

A comprehensive platform enabling flexible school fee payments through M-Pesa, featuring installment plans, micro-loans, credit scoring, and advanced analytics.

## Features

### Core Payment Features
- **M-Pesa STK Push Integration** - Seamless mobile payments via Safaricom M-Pesa
- **Payment Tracking** - Real-time payment status and history
- **Invoice Management** - Create and track fee invoices per student

### Flexible Payment Options
- **Installment Plans** - Split large fees into manageable monthly payments
- **Automated Scheduling** - Auto-generate payment schedules with due dates
- **Late Fee Management** - Configurable late payment penalties

### Embedded Finance (Micro-Loans)
- **Loan Applications** - Apply for school fee loans
- **Credit Scoring** - Automated credit assessment based on payment history
- **Risk Assessment** - Default probability prediction
- **Repayment Tracking** - Monitor loan repayments with amortization schedules

### Analytics & Reporting
- **Collection Metrics** - Track collection rates and outstanding balances
- **Payment Patterns** - Analyze timing and amount distributions
- **Timeliness Reports** - On-time vs late payment analysis
- **Predictive Analytics** - Forecast future collections
- **Risk Identification** - Identify at-risk students early

### Security Features
- **Rate Limiting** - Protect against abuse
- **Input Validation** - Comprehensive sanitization
- **Audit Logging** - Track all sensitive operations
- **Credential Protection** - Secure M-Pesa credential handling
- **Security Headers** - OWASP recommended headers

## Tech Stack

- **Framework**: FastAPI (Python 3.10+)
- **Database**: SQLAlchemy with async support (SQLite/PostgreSQL)
- **Payments**: Safaricom M-Pesa API
- **Validation**: Pydantic v2

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Configuration management
│   ├── middleware.py        # Rate limiting, security headers
│   ├── models/
│   │   ├── database.py      # Database connection
│   │   └── payment.py       # All SQLAlchemy models
│   ├── routes/
│   │   ├── payments.py      # M-Pesa payment endpoints
│   │   ├── schools.py       # School management
│   │   ├── guardians.py     # Guardian/parent management
│   │   ├── students.py      # Student management
│   │   ├── invoices.py      # Invoice management
│   │   ├── installments.py  # Installment plans
│   │   ├── loans.py         # Micro-loans & credit scoring
│   │   ├── analytics.py     # Reporting & analytics
│   │   └── schemas.py       # Pydantic schemas
│   └── services/
│       ├── mpesa.py         # M-Pesa API integration
│       ├── credit_scoring.py # Credit score calculation
│       ├── analytics.py     # Analytics engine
│       └── security.py      # Security utilities
├── requirements.txt
└── .env.example
```

## API Endpoints

### Payments
- `POST /api/v1/payments/initiate` - Initiate M-Pesa STK Push
- `POST /api/v1/payments/callback` - M-Pesa callback handler
- `GET /api/v1/payments/status/{transaction_id}` - Check payment status
- `GET /api/v1/payments/` - List payments

### Installment Plans
- `POST /api/v1/installments/plans` - Create installment plan
- `GET /api/v1/installments/plans` - List plans
- `GET /api/v1/installments/plans/{plan_id}/schedule` - Get payment schedule
- `POST /api/v1/installments/plans/{plan_id}/installments/{num}/pay` - Pay installment

### Loans
- `GET /api/v1/loans/credit-score/{guardian_id}` - Get/calculate credit score
- `GET /api/v1/loans/eligibility/{guardian_id}` - Check loan eligibility
- `POST /api/v1/loans/apply` - Submit loan application
- `POST /api/v1/loans/{loan_id}/approve` - Approve/reject loan
- `POST /api/v1/loans/{loan_id}/disburse` - Disburse approved loan
- `GET /api/v1/loans/{loan_id}/repayments` - Get repayment schedule

### Analytics
- `GET /api/v1/analytics/collections/overview` - Collection metrics
- `GET /api/v1/analytics/collections/trends` - Payment trends
- `GET /api/v1/analytics/patterns/analysis` - Payment pattern analysis
- `GET /api/v1/analytics/patterns/timeliness` - On-time vs late analysis
- `GET /api/v1/analytics/predictions/collections` - Forecast collections
- `GET /api/v1/analytics/predictions/at-risk-students` - Identify at-risk students
- `GET /api/v1/analytics/dashboard/summary` - Dashboard data

### Core Resources
- `/api/v1/schools/` - School CRUD operations
- `/api/v1/guardians/` - Guardian CRUD operations
- `/api/v1/students/` - Student CRUD operations
- `/api/v1/invoices/` - Invoice CRUD operations

## Setup

### Prerequisites
- Python 3.10+
- Safaricom Developer Account (for M-Pesa)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-repo/flexifees.git
cd flexifees/backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your M-Pesa credentials
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

6. Access API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MPESA_CONSUMER_KEY` | Safaricom API consumer key | Yes |
| `MPESA_CONSUMER_SECRET` | Safaricom API consumer secret | Yes |
| `MPESA_SHORTCODE` | Business shortcode | Yes |
| `MPESA_PASSKEY` | Online passkey | Yes |
| `MPESA_CALLBACK_URL` | Callback URL for payment notifications | Yes |
| `DATABASE_URL` | Database connection string | Yes |
| `ENVIRONMENT` | `sandbox` or `production` | No |
| `DEBUG` | Enable debug mode | No |
| `MOCK_MPESA` | Use mock M-Pesa responses | No |

## Credit Scoring Model

The credit scoring system uses a weighted model:

| Component | Weight | Description |
|-----------|--------|-------------|
| Payment History | 35% | On-time vs late vs missed payments |
| Credit Utilization | 30% | Outstanding balance ratio |
| Length of History | 15% | Duration of payment history |
| Payment Consistency | 20% | Regularity of payments |

Score Range: 300-850

Risk Levels:
- **Low Risk** (700+): Eligible for best loan terms
- **Medium Risk** (550-699): Standard loan terms
- **High Risk** (400-549): Higher interest, shorter tenure
- **Very High Risk** (<400): Not eligible for loans

## Security Considerations

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Use HTTPS in production** - All API calls must be encrypted
3. **Validate callback signatures** - Ensure M-Pesa callbacks are authentic
4. **Monitor audit logs** - Review for suspicious activity
5. **Regular credential rotation** - Change API keys periodically

## Data Science Integration

The analytics endpoints provide data for:
- Payment prediction models
- Credit scoring model training
- Collection strategy optimization
- Risk assessment algorithms

Export endpoints available:
- `/api/v1/analytics/export/payment-data` - Full payment history
- `/api/v1/analytics/export/credit-scores` - Credit score dataset

## License

MIT License

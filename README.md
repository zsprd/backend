# ZSPRD Portfolio Analytics - FastAPI Backend

Professional portfolio analytics API for high-net-worth individuals. This FastAPI backend provides comprehensive financial calculations, risk analysis, and portfolio management capabilities.

## 🚀 Quick Start

### Prerequisites

-   **Python 3.11+** installed
-   **PostgreSQL** running locally with database `zsprd_dev`
-   **Alpha Vantage API key** (free tier is fine)

### Step 1: Clone and Setup

```bash
# Create the project directory
mkdir backend
cd backend

# Copy all the files from the artifacts into this directory
# (The folder structure, .env, requirements.txt, main.py, etc.)
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Open `.env` and fill in all required secrets and configuration values. **Do not use example or default secrets in
   production.**

Example `.env` (do not commit this file):

```
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
SECRET_KEY=your-super-secret-key
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<db>
```

### Step 4: Test Database Connection

```bash
# Test if your PostgreSQL setup is working
python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://zsprd_dev:secure@localhost:5432/zsprd_dev')
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

### Step 5: Run the API

```bash
# Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

🎉 **Your API is now running!**

-   **API Docs**: http://localhost:8000/api/v1/docs
-   **ReDoc**: http://localhost:8000/api/v1/redoc
-   **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
fastapi-backend/
├── .env                     # Environment variables
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── main.py                # FastAPI app entry point
├── setup.py               # Setup script
│
├── app/
│   ├── core/              # Core configuration
│   │   ├── config.py      # Settings
│   │   ├── database.py    # DB connection
│   │   └── auth.py        # JWT authentication
│   │
│   ├── models/            # SQLAlchemy models
│   │   ├── enums.py       # Database enums
│   │   ├── base.py        # Base model
│   │   ├── user.py        # User model
│   │   ├── account.py     # Account models
│   │   └── security.py    # Security model
│   │
│   ├── api/v1/            # API endpoints
│   │   ├── router.py      # Main router
│   │   ├── deps.py        # Dependencies
│   │   └── accounts.py    # Account endpoints
│   │
│   ├── services/          # Business logic
│   │   └── analytics_service.py  # Financial analytics
│   │
│   └── utils/             # Utilities
│       └── calculations.py       # Financial calculations
│
└── tests/                 # Test files
```

## 🔑 API Authentication

The API uses JWT tokens for authentication. Your NextJS frontend should send tokens in the Authorization header:

```
Authorization: Bearer <jwt-token>
```

The backend will extract the `user_id` from the JWT payload (`sub` field).

## 📊 Available Endpoints

### Accounts

-   `GET /api/v1/accounts/` - List user's accounts
-   `POST /api/v1/accounts/` - Create new account
-   `GET /api/v1/accounts/{id}` - Get account details
-   `PUT /api/v1/accounts/{id}` - Update account
-   `DELETE /api/v1/accounts/{id}` - Deactivate account

### Analytics (Coming Soon)

-   `GET /api/v1/analytics/performance` - Portfolio performance metrics
-   `GET /api/v1/analytics/risk` - Risk analysis
-   `GET /api/v1/analytics/allocation` - Asset allocation breakdown

### Holdings & Transactions (Coming Soon)

-   Portfolio holdings management
-   Transaction history and analysis
-   Market data integration

## 🧮 Financial Analytics

The backend provides sophisticated financial calculations:

### Performance Metrics

-   Total Return, Annualized Return
-   Volatility (Standard Deviation)
-   Sharpe Ratio, Sortino Ratio
-   Maximum Drawdown
-   Calmar Ratio

### Risk Analysis

-   Value at Risk (VaR) at 90%, 95%, 99%
-   Conditional VaR (Expected Shortfall)
-   Beta vs. benchmarks
-   Correlation analysis
-   Downside deviation

### Allocation Analysis

-   Asset type breakdown
-   Sector allocation
-   Geographic exposure
-   Currency allocation
-   Concentration risk

## 🔧 Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
```

### Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Create initial tables"

# Apply migration
alembic upgrade head
```

## 🚀 Deployment

### Railway Deployment

1. **Prepare for deployment**:

```bash
# Create Procfile for Railway
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Create railway.json
echo '{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}' > railway.json
```

2. **Environment Variables on Railway**:

    - `DATABASE_URL` - Railway PostgreSQL URL
    - `SECRET_KEY` - Generate secure key
    - `ALPHA_VANTAGE_API_KEY` - Your API key
    - `ENVIRONMENT=production`
    - `DEBUG=False`

3. **Deploy**:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

## 📈 Alpha Vantage Integration

The backend integrates with Alpha Vantage for market data:

-   **Free Tier**: 5 API calls per minute, 500 per day
-   **Rate Limiting**: Built-in to respect API limits
-   **Caching**: Market data cached for 1 hour
-   **Symbols**: Supports stocks, ETFs, cryptocurrencies

## 🔒 Security Features

-   **JWT Token Validation**
-   **CORS Protection**
-   **Rate Limiting**
-   **Input Validation**
-   **SQL Injection Prevention**
-   **Secure Headers**

## 🤝 Integration with NextJS Frontend

### Example API Call from Frontend:

```typescript
// In your NextJS app
const response = await fetch('http://localhost:8000/api/v1/accounts', {
	headers: {
		Authorization: `Bearer ${session.accessToken}`,
		'Content-Type': 'application/json'
	}
});
const accounts = await response.json();
```

### TanStack Query Integration:

```typescript
// hooks/useAccounts.ts
import { useQuery } from '@tanstack/react-query';

export const useAccounts = () =>
	useQuery({
		queryKey: ['accounts'],
		queryFn: () => fetch('/api/v1/accounts').then((res) => res.json()),
		staleTime: 5 * 60 * 1000 // 5 minutes
	});
```

## 📞 Support

For development questions or issues:

1. Check the **API documentation** at `/docs`
2. Review the **logs** for error messages
3. Ensure your **database** connection is working
4. Verify your **environment variables**

## 🎯 Next Steps

After getting the basic API running:

1. **Complete the missing models** (holdings, transactions, market_data)
2. **Implement CRUD operations** for all entities
3. **Add the analytics endpoints**
4. **Set up Alembic migrations**
5. **Add comprehensive tests**
6. **Implement market data fetching**
7. **Add caching with Redis**

Happy coding! 🚀

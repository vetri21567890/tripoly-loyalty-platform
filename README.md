# Tripoly Loyalty Platform

Production-ready travel loyalty platform with FastAPI backend and React customer/admin portals.

## Architecture

- **Coins = Points** (Tripoly Coins)
- **Tier qualification**: Lifetime Coins Earned (redemption does not reduce tier)
- **Wallet**: Lot-based FIFO redemption (earliest expiry first, non-expiring last)
- **Referral**: Reward issued only after referred customer's first confirmed booking
- **UGC**: Coins issued only after admin approval
- **Partner APIs**: Booking confirmation, customer sync, referral validation, coin issuance

## Quick Start

### Docker (recommended)

```bash
cd tripoly
docker compose up --build
```

- API: http://localhost:8000/docs
- Customer portal: http://localhost:5173
- Admin portal: http://localhost:5174

### Seed database

```bash
docker compose exec api python scripts/seed.py
```

Default admin: `admin@tripoly.app` / `Admin@12345`

Partner API key header: `X-Api-Key: dev-partner-key-change-in-production`

### Local backend only

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Start PostgreSQL, then:
python scripts/seed.py
uvicorn app.main:app --reload
```

## Project Structure

```
tripoly/
  backend/          # FastAPI + SQLAlchemy + Alembic
  frontend/
    customer/       # React customer portal
    admin/          # React admin portal
  docker-compose.yml
```

## Key Endpoints

| Module | Base |
|--------|------|
| Auth | `/api/v1/auth` |
| Wallet | `/api/v1/wallet` |
| Rewards | `/api/v1/rewards` |
| Referrals | `/api/v1/referrals` |
| UGC | `/api/v1/ugc` |
| Admin | `/api/v1/admin` |
| Partner | `/api/integrations` |

## OTP (development)

OTP codes are logged to the API container stdout when verifying phone login.

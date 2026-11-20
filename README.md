# E-Commerce Shopping Cart API — Automated Testing Project

A REST API for e-commerce shopping cart operations built with **Flask** and **SQLite**, with comprehensive API test automation using **Python Unittest**, **SoapUI**, and **GitHub Actions CI/CD**.

---

## Features

- Product catalog management with stock tracking
- Shopping cart — add, update, remove items with stock validation
- Discount coupons — percentage and flat discounts with minimum order rules
- Checkout with order creation, stock deduction, and discount application
- Order history and details
- Database reset endpoint for test isolation

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11, Flask 3.x |
| Database | SQLite |
| Unit Testing | Pytest / Unittest |
| API Testing | SoapUI 5.7.2 |
| CI/CD | GitHub Actions |
| API Spec | OpenAPI 3.0 |

---

## Project Structure

```
Ecommerce_Cart_API_Testing/
├── app.py                        # Flask API application
├── openapi.json                  # OpenAPI 3.0 specification
├── requirements.txt              # Python dependencies
├── tests/
│   └── test_api.py               # Unit & integration tests
├── soapui/
│   └── Ecommerce-Cart-SoapUI-Project.xml
├── scripts/
│   ├── generate_soapui_project.py
│   ├── run_all.py
│   ├── run_soapui_tests.bat
│   ├── run_soapui_tests.ps1
│   └── stop_server.bat
├── reports/soapui/               # Generated test reports
└── .github/workflows/
    └── api-testing.yml           # CI/CD pipeline
```

---

## Setup & Installation

```bash
# Clone the repository
git clone https://github.com/Manjunathaumashankar/Ecommerce_Cart_API_Testing.git
cd Ecommerce_Cart_API_Testing

# Install dependencies
pip install -r requirements.txt

# Start the API server
python app.py
```

API runs at: `http://127.0.0.1:5000`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/products` | List all products |
| `GET` | `/products/<id>` | Get product by ID |
| `POST` | `/cart` | Add product to cart |
| `GET` | `/cart` | View cart with totals and discount |
| `PUT` | `/cart/<id>` | Update cart item quantity |
| `DELETE` | `/cart/<id>` | Remove item from cart |
| `DELETE` | `/cart` | Clear entire cart |
| `GET` | `/coupons` | List discount coupons |
| `POST` | `/cart/apply-coupon` | Apply coupon to cart |
| `DELETE` | `/cart/coupon` | Remove applied coupon |
| `POST` | `/cart/checkout` | Checkout and place order |
| `GET` | `/orders` | List all orders |
| `GET` | `/orders/<id>` | Get order details |
| `POST` | `/reset` | Reset database to default state |

---

## Sample Data

### Products

| ID | Name | Price (₹) | Stock |
|----|------|-----------|-------|
| 1 | Laptop | 55,000 | 10 |
| 2 | Smartphone | 20,000 | 15 |
| 3 | Headphones | 1,500 | 25 |
| 4 | Keyboard | 800 | 20 |
| 5 | Mouse | 500 | 30 |

### Discount Coupons

| Code | Type | Value | Min Order | Status |
|------|------|-------|-----------|--------|
| `SAVE10` | Percentage | 10% | ₹1,000 | Active |
| `FLAT500` | Flat | ₹500 | ₹2,000 | Active |
| `MEGA20` | Percentage | 20% | ₹10,000 | Active |
| `EXPIRED50` | Percentage | 50% | ₹500 | Inactive |

---

## Running Tests

### Python Unit & Integration Tests

```bash
python -m unittest discover -s tests -p "test_*.py"

# or
pytest tests/ -v
```

### SoapUI Tests

```powershell
.\scripts\run_soapui_tests.ps1       # PowerShell
.\scripts\run_soapui_tests.bat       # Command Prompt
```

### Run All Tests

```bash
python scripts/run_all.py
```

---

## SoapUI Test Suites

| # | Test Suite | Coverage |
|---|------------|----------|
| 1 | Smoke & Sanity | Health check, product listing, coupons |
| 2 | Shopping Cart E2E Workflow | Add to cart → apply coupon → checkout → verify stock |
| 3 | Discount Coupon Functionality | Apply, validate, and remove coupons |
| 4 | Cart Management & Deletion | Add, update, delete cart items |
| 5 | Negative & Boundary Validations | Invalid inputs, empty cart, expired coupons |
| 6 | Dynamic Property Transfer | Dynamic ID extraction and reuse across test steps |

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/api-testing.yml`) triggers on every push and pull request:

1. Sets up Python 3.11 and Java JDK 17
2. Installs project dependencies
3. Runs Python unit and integration tests
4. Starts the Flask API server
5. Executes SoapUI TestRunner against the live API
6. Uploads test reports as artifacts

---

## API Usage Examples

```bash
# Add item to cart
curl -X POST http://127.0.0.1:5000/cart \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# Apply discount coupon
curl -X POST http://127.0.0.1:5000/cart/apply-coupon \
  -H "Content-Type: application/json" \
  -d '{"code": "SAVE10"}'

# View cart
curl http://127.0.0.1:5000/cart

# Checkout
curl -X POST http://127.0.0.1:5000/cart/checkout
```

---

## Author

**Manjunatha**

---

## License

This project is for educational and portfolio purposes.

# Jodo Developer Portal - Handoff Document (V2 - Sandbox Evolution)

This document tracks the current state, architecture, and progress of the Jodo Developer Portal integration project.

## 🚀 V6 - Production Persistence & Standardized PG Behavior
The sandbox has been upgraded to match industry-standard payment gateway behavior (Razorpay/Easebuzz style) and uses a persistent database.

### 1. Standardized API Response
The `create_order` API now returns the following standard structure:
```json
{
    "status": "success",
    "data": {
        "order_id": "order_xyz123",
        "redirect_url": "https://your-domain.com/pay/order_xyz123"
    }
}
```

### 2. Automatic Redirection (Merchant Callback)
After a successful payment simulation:
- The checkout page waits **2 seconds** (for the success checkmark).
- It then **automatically redirects** the browser to the merchant's `callback_url`.
- URL Parameters included: `?order_id=...&status=paid&payment_id=...`

### 3. Data Persistence (Free PostgreSQL Guide)
Since Render's free tier disables persistent disks, we use its **Free PostgreSQL Service** for durable storage. 

**Setup Steps:**
1. In your **Render Dashboard**, click **New +** -> **PostgreSQL**.
2. **Name**: `jodo-sandbox-db`
3. **Instance Type**: Select **Free** (lasts 90 days, renewable).
4. After creation, go to the **Connect** button and copy the **Internal Database URL**.
5. Go to your **Web Service** (the main app) -> **Environment**.
6. Add a new Environment Variable:
   - **Key**: `DATABASE_URL`
   - **Value**: (Paste the URL you copied)
7. Save changes. The app will automatically migrate from local SQLite to Postgres!

### 4. Master Demo Key
- **Key**: `jodo_sb_MASTER_KEY`
- **Utility**: Always works. Orders created with this key automatically "adopt" the developer's current dashboard session if they are logged in.

## 🛠 Tech Stack
- **Backend:** Python (Flask) - Service-Oriented Package Architecture
- **Frontend:** Vanilla HTML5, CSS3 (Glassmorphic UI), JavaScript
- **Database:** SQLite (`data/sandbox.db`)
- **Notifications:** Telegram Bot Integration (Notifications & Remote Approval)
- **API Simulation:** Realistic Sandbox supporting Jodo, Razorpay, and Easebuzz.

## 📁 Project Structure
- `server.py`: Entry point for the Flask application.
- `app/`: Main application package.
  - `auth/`: Developer credentials and Console routing (`/console`).
  - `orders/`: Persistent order engine with status lifecycle.
  - `webhooks/`: Async delivery and retry logic with logging.
  - `simulation/`: Mock checkout experience (`/pay/<id>`).
  - `utils/`: Storage, notification, and common helpers.
- `dashboard/`: Static assets for the developer console.
- `data/`: Directory for JSON data persistence.
- `checkout.html`: Template for the simulated payment experience.

## ✨ Key Features (Sandbox Evolution)
- [x] **Modular Architecture:** Cleanly separated concerns for better maintainability.
- [x] **Persistent Order Engine:** Full status tracking (`created` → `paid` → `settled` / `failed`).
- [x] **Webhook Simulation System:** Async delivery with exponential backoff (3 retries).
- [x] **Event Filtering:** Selective delivery based on configured events (e.g., `order.paid`) per endpoint.
- [x] **Delivery Logs:** Transparent history of all webhook events and response codes.
- [x] **Premium Checkout UI:** Glassmorphic, low-latency simulator for testing customer-facing flows.
- [x] **Interactive Console:** Enhanced Dashboard and Playground for rapid testing.
- [x] **Remote Differential Approval:** Human-in-the-loop review for codebase changes via Telegram.

## 🏁 Current Status
- The system is now a **Production-Grade Sandbox**.
- **Local Access:** `python3 server.py` (http://localhost:5001)
- **Cloud Deployment:** Ready for `Digital Ocean App Platform` (WSGI/Gunicorn).

## 📋 Next Steps / Roadmap
- [x] **Cloud-Ready Deployment:** Complete set of metadata for one-click hosting.
- [ ] Connect a managed PostgreSQL/Redis for persistent user sessions in the cloud.
- [ ] Add "Production-Ready" validation tool to the console.
- [ ] Finalize "Gold Standard" documentation for all webhook response types.

---
*Last Updated: 2026-04-02 (Jodo Sandbox Evolution V5 - Cloud Ready)*

# HSE Observation Reporting POC

A full-stack web application for analyzing HSE (Health, Safety & Environment) observation Excel reports. Upload an Excel file, view interactive charts and an AI-generated executive summary, then email the full report to a VP.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + Tailwind CSS + Chart.js |
| Backend | Python FastAPI |
| Excel parsing | pandas + openpyxl |
| AI summary | Azure OpenAI (GPT-4) |
| Email charts | matplotlib |
| Email delivery | SMTP (Gmail / Outlook) |

---

## Project Structure

```
hse-poc/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── models/schemas.py        # Pydantic models
│   ├── services/
│   │   ├── excel_service.py     # Excel parsing
│   │   ├── openai_service.py    # Azure OpenAI
│   │   ├── chart_service.py     # matplotlib charts
│   │   └── email_service.py     # SMTP email
│   ├── .env.example
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api/client.js
    │   └── components/
    │       ├── FileUpload.jsx
    │       ├── Dashboard.jsx
    │       ├── ChartGrid.jsx
    │       ├── SummaryPanel.jsx
    │       └── EmailModal.jsx
    └── package.json
```

---

## Setup

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env
# Edit .env and fill in your Azure OpenAI + SMTP credentials
```

### 2. Frontend

```bash
cd frontend
npm install
```

---

## Environment Variables

Edit `backend/.env` with your credentials:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01

# SMTP (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password   # Google App Password, not account password
SMTP_FROM=your_email@gmail.com
```

**Gmail note:** Enable 2-Step Verification, then create an App Password at
https://myaccount.google.com/apppasswords — use that as `SMTP_PASSWORD`.

**Outlook note:** Use `smtp.office365.com` port `587`.

---

## Running the App

Open **two terminals**:

**Terminal 1 — Backend:**
```bash
cd backend
# activate venv first if not active
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Excel File Format

The app expects an Excel file with these column headers (row 1):

| Column | Values |
|--------|--------|
| Observation Date | date |
| Facility | text |
| Description | text |
| Observation Category | text |
| Type of observation | `Safe` or `At Risk` |
| Stop work authority | `Yes` / `No` |
| Corrective Actions Taken | text |

> The parser handles minor header variations (whitespace, typos in "Category").

---

## User Flow

1. **Upload** — drag & drop or click to browse for your `.xlsx` file
2. **Auto-process** — app parses the data and calls Azure OpenAI for the summary (~10-20 seconds)
3. **Dashboard** — view 4 interactive charts + KPI cards + AI executive summary
4. **Email** — click "Send Email Report", enter the VP's email address, click Send

The email contains:
- HTML-formatted executive summary
- All 4 charts embedded inline (no attachments to open)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/upload` | Parse Excel file → return chart data |
| POST | `/api/summarize` | Generate AI summary via Azure OpenAI |
| POST | `/api/send-email` | Generate chart PNGs + send HTML email |

# Kith Platform - Personal Intelligence Platform

A private, web-based Personal Intelligence Platform that leverages AI to parse, categorize, and synthesize unstructured conversational notes about your relationships.

## Features

### Phase 1 (MVP) ✅ Complete
- **AI-Powered Analysis**: Uses Gemini Pro to analyze notes and categorize information into 20 detailed categories
- **RAG Pipeline**: Retrieves relevant history from ChromaDB for context-aware analysis
- **Quality-First Design**: Prioritizes analysis quality over speed or cost
- **Clean, Utilitarian UI**: Minimalist interface focused on functionality
- **Privacy-First**: Single-tenant, private web application

### Phase 2 ✅ Complete
- **VCard Contact Import**: Bulk import contacts from .vcf files with duplicate detection
- **360° Profile View**: Display all 20 categories of information for each contact
- **Robust Search**: Keyword + semantic search across contacts and their data
- **Tier Filtering**: Filter contacts by Tier 1 (inner circle) vs Tier 2
- **Contact Management**: Full CRUD operations for contacts
- **Database Integration**: SQLite for development, PostgreSQL ready for production

### Phase 3 ✅ Complete
- **Telegram Chat Scraper**: Local script for ingesting chat history
- **Proactive Notifications**: Email digests with actionable items and event reminders
- **Automated Analysis**: Automatic processing and saving of chat transcripts
- **Scheduled Jobs**: Weekly actionable items digest and daily event checks

### Phase 4 ✅ Complete
- **Advanced Analytics**: Relationship health scoring and trend analysis
- **Calendar Integration**: Automatic event creation from actionable items
- **Smart NLP**: Date/time extraction from natural language
- **Network Insights**: Comprehensive relationship network analysis
- **Personalized Recommendations**: AI-powered relationship improvement suggestions

## Quick Start

### Local Development

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd kith-platform
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   # Copy and edit the .env file
   cp .env.example .env
   # Add your Gemini API key to .env
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```
   The app will be available at `http://localhost:5001`

### Phase 3 Setup (Optional)

1. **Telegram Configuration**
   ```bash
   # Get API credentials from https://my.telegram.org
   # Add to .env:
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   ```

2. **Email Configuration (Optional)**
   ```bash
   # Add to .env for notifications:
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   EMAIL_RECIPIENT=your_email@gmail.com
   ```

3. **Start Scheduler (Optional)**
   ```bash
   python scheduler.py
   ```

### Testing

Run the automated test suite:
```bash
python -m pytest test_app.py -v
```

Run with coverage:
```bash
python -m pytest test_app.py --cov=app --cov-report=html
```

### Deployment to Render.com

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Phase 3 complete: Telegram integration and proactive notifications"
   git push origin main
   ```

2. **Deploy on Render**
   - Connect your GitHub repository to Render.com
   - Create a new Web Service
   - Render will automatically detect the `render.yaml` configuration
   - Set environment variables:
     - `GEMINI_API_KEY`: Your Google AI Studio API key
     - `DATABASE_URL`: PostgreSQL connection string (optional for MVP)

3. **Environment Variables**
   - `GEMINI_API_KEY`: Required for AI analysis
   - `DATABASE_URL`: PostgreSQL URL (for future database integration)
   - `TELEGRAM_API_ID`: Telegram API ID (for Phase 3)
   - `TELEGRAM_API_HASH`: Telegram API Hash (for Phase 3)
   - `EMAIL_*`: Email configuration (for Phase 3 notifications)

## Architecture

### Backend (Python/Flask)
- **Framework**: Flask
- **AI Integration**: Google Generative AI (Gemini Pro)
- **Vector Database**: ChromaDB (local for MVP)
- **Database**: SQLAlchemy with SQLite/PostgreSQL
- **Testing**: pytest with comprehensive test coverage (70%+)

### Frontend
- **Structure**: Plain HTML/CSS/JavaScript
- **Design**: Utilitarian, minimalist, information-dense
- **Interactions**: Fetch API for backend communication

### Phase 3 Components
- **Telegram Scraper**: Standalone script using Telethon library
- **Scheduler**: Background process using schedule library
- **Email Notifications**: SMTP integration for proactive alerts

### Data Flow
1. User imports contacts via VCard or creates them manually
2. User inputs unstructured note for a specific contact
3. Backend retrieves relevant history from ChromaDB
4. AI analyzes note with context using Gemini Pro
5. Results are categorized into 20 predefined categories
6. User reviews and approves the analysis
7. Data is saved to database for future retrieval
8. **Phase 3**: Telegram transcripts automatically processed
9. **Phase 3**: Scheduled notifications sent via email

## API Endpoints

### Contact Management
- `GET /api/contacts` - Get all contacts
- `POST /api/import-vcard` - Import contacts from VCard file
- `GET /api/contact/<id>` - Get 360° profile for a contact

### Note Processing
- `POST /api/process-note` - Process a new note with AI analysis
- `POST /api/save-synthesis` - Save approved analysis to database

### Phase 3 - Automation
- `POST /api/process-transcript` - Process Telegram chat transcripts (authenticated)

### Phase 4 - Analytics & Calendar
- `GET /api/analytics/contact/<id>/health` - Get relationship health score
- `GET /api/analytics/contact/<id>/trends` - Get relationship trends
- `GET /api/analytics/contact/<id>/recommendations` - Get personalized recommendations
- `GET /api/analytics/network` - Get network insights
- `GET /api/calendar/events` - Get upcoming calendar events
- `POST /api/calendar/create-from-actionable` - Create events from actionable items
- `POST /api/calendar/extract-datetime` - Extract date/time from text

### Search & Discovery
- `GET /api/search?q=<query>` - Search contacts and notes

### System
- `GET /health` - Health check endpoint

## Development Guidelines

### Code Quality
- All code must be debuggable and well-documented
- Comprehensive test coverage for all endpoints (70%+)
- Error handling for all external API calls
- Quality of analysis takes priority over speed

### Testing Strategy
- Unit tests for all API endpoints
- Mocked external dependencies (Gemini API, ChromaDB)
- Error condition testing
- Environment configuration validation

### Deployment
- Automated deployment via Render.com
- Environment variable management
- Health check endpoints
- Production-ready WSGI server (gunicorn)

## Current Status

### ✅ Phase 1 Complete
- Core AI analysis engine
- RAG pipeline with ChromaDB
- Basic note input and review
- Health monitoring

### ✅ Phase 2 Complete
- VCard contact import
- 360° profile view
- Advanced search (keyword + semantic)
- Tier-based contact filtering
- Database integration
- Comprehensive testing

### ✅ Phase 3 Complete
- Telegram chat ingestion
- Proactive notifications
- Email digest system
- Automated transcript processing
- Scheduled background jobs

### ✅ Phase 4 Complete
- Advanced analytics with health scoring
- Calendar integration with NLP
- Network insights and trends
- Personalized recommendations
- Smart date/time extraction

## Usage Examples

### Basic Note Processing
```bash
# Start the platform
python app.py

# Access web interface
open http://localhost:5001
```

### Telegram Integration
```bash
# Check configuration
python telegram_config.py

# Scrape chat history
python telegram_scraper.py username --days 30 --contact-id 1
```

### Proactive Notifications
```bash
# Start scheduler
python scheduler.py

# Check logs
tail -f scheduler.log
```

## Troubleshooting

### Common Issues

1. **Flask app won't start**
   - Check virtual environment is activated
   - Verify all dependencies are installed
   - Check `.env` file configuration

2. **AI analysis fails**
   - Verify Gemini API key is correct
   - Check internet connectivity
   - Review API rate limits

3. **VCard import issues**
   - Ensure file is properly formatted (.vcf extension)
   - Check file encoding (UTF-8)
   - Verify VCard syntax

4. **Telegram scraper issues**
   - Ensure API credentials are correct
   - Check that the username exists
   - Verify the contact is in your Kith database

5. **Email notifications not working**
   - Use App Passwords for Gmail
   - Check firewall settings
   - Verify SMTP settings

6. **Database errors**
   - Ensure write permissions in project directory
   - Check available disk space
   - Verify SQLite file is not corrupted

### Debug Mode
The app runs in debug mode locally. Check the console for detailed error messages and stack traces.

## License

Private project - not for distribution. 

# Kith Platform - Developer Guide

## Prerequisites
- Python 3.11+
- Virtualenv

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment
Create a `.env` file in `kith-platform/`:
```
OPENAI_API_KEY=
KITH_API_TOKEN=dev_token
CHROMA_DB_PATH=/absolute/path/to/chroma_db  # optional; defaults to kith-platform/chroma_db
ANONYMIZED_TELEMETRY=FALSE                 # disable Chroma telemetry
KITH_DB_PATH=/absolute/path/to/kith_platform.db  # optional; override DB file
```

## Running (Development)
```bash
source .venv/bin/activate
FLASK_ENV=development python app.py
```
The app listens on `http://0.0.0.0:5001` by default (see `constants.py`).

## Running (Production)
Use gunicorn:
```bash
gunicorn -w 2 -k gevent -b 0.0.0.0:5001 app:app
```
Or uvicorn workers for ASGI via `uvicorn`/`hypercorn` if needed.

## Background Workers
- Telegram importer runs via `telegram_worker.py` through `/api/telegram/start-import`.
- Reindex job: POST `/api/reindex/start` then GET `/api/reindex/status/<task_id>` to poll progress.

## Testing
```bash
pytest -q
```

## Linting & Formatting
```bash
flake8
black --check .
isort --check-only .
```

## Pre-commit
Install and enable hooks locally:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Health/Readiness
- Health endpoint: `GET /api/health` (returns app status)
- Readiness: `GET /api/ready` (ensures DB and Chroma are reachable)

## CSV Export
`GET /api/export/csv` returns a record-type CSV with lineage fields. 
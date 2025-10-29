# Project Notes Manager

A web-based Streamlit application for project note-taking with automatic cleanup and categorization using xAI's Grok API.

## Features

- **Smart Note Processing**: Automatically clean and categorize notes using AI
- **Approval Workflow**: Review and edit AI-processed notes before saving
- **Multiple Views**:
  - Daily chronological view
  - Categorized view with 27+ project categories
  - Table export to CSV
- **Pagination**: Efficient handling of large note collections
- **Database Backup**: Create on-demand backups
- **Activity Logging**: Track all user actions and API calls

## Quick Start

### 1. Prerequisites

- Python 3.9 or higher
- xAI API key ([Get one here](https://x.ai))

### 2. Installation

```bash
# Clone or navigate to the project directory
cd aes_note_taking_app

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your xAI API key
# Windows: notepad .env
# macOS/Linux: nano .env
```

**Required environment variables:**
```
XAI_API_KEY=your_api_key_here
```

**Optional environment variables:**
```
AUTH_ENABLED=False        # Set to True to enable authentication
ADMIN_USERNAME=admin      # Admin username if auth enabled
ADMIN_PASSWORD=changeme   # Admin password if auth enabled
LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 4. Run the Application

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

## Project Structure

```
aes_note_taking_app/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── README.md                # This file
│
├── config/                  # Configuration files
│   ├── settings.py         # App settings and constants
│   └── categories.py       # Predefined project categories
│
├── database/               # Database layer
│   ├── db_manager.py      # SQLite operations
│   └── models.py          # Data models and schemas
│
├── api/                   # External API integration
│   └── xai_client.py     # xAI Grok API client
│
├── ui/                   # UI components
│   ├── input_view.py    # Note input interface
│   ├── approval_view.py # Note approval interface
│   ├── daily_view.py    # Chronological view
│   └── categorized_view.py # Category-based view
│
├── utils/               # Utilities
│   ├── logger.py       # Logging configuration
│   └── validators.py   # Input validation
│
├── data/               # Data directory (created automatically)
│   ├── notes.db       # SQLite database
│   └── backups/       # Database backups
│
├── logs/              # Log files (created automatically)
│   └── app.log       # Application logs
│
└── tests/            # Test files
    └── (tests to be added)
```

## Usage Guide

### Creating Notes

1. Go to the **"New Note"** tab
2. Enter your project notes in the text area
3. Click **"Submit Notes"**
4. AI will process and categorize your notes
5. Review in the **"Approve Notes"** tab

### Approving Notes

1. Go to the **"Approve Notes"** tab
2. Review the original vs. cleaned text
3. Edit text or change category if needed
4. Click:
   - **Approve** to save the note
   - **Reject** to mark it as rejected
   - **Delete** to remove it entirely

### Viewing Notes

**Daily View:**
- View notes chronologically by date
- Filter by date range
- Notes grouped by day with timestamps

**Categorized View:**
- View notes organized by category
- Filter by category and date range
- Choose between grouped view or table view
- Export to CSV

### Database Backups

1. Click **"Create Backup"** in the sidebar
2. Backup saved to `data/backups/` with timestamp

## Configuration

### Predefined Categories

The app uses 27 predefined categories from project management:

- General
- Development/Reliance Material
- GIS updates
- Interconnection
- Land
- Facility location
- Environmental/Biological Cultural
- Schedule
- Breakers, MPT, Modules
- Owner's Engineer
- 30% Package, 60% Package
- Geotech investigation
- Structural, Civil, Electrical
- Substation
- Construction Milestones
- Pricing, Risk Register
- Permanent Utilities
- Contracting, LNTP, BOP-EPC, PWC
- Action Items

**To modify categories**: Edit `config/categories.py`

### Performance Settings

Current settings in `config/settings.py`:

- **Pagination**: 50 notes per page
- **API Retries**: 3 attempts with exponential backoff (1s, 2s, 4s)
- **API Timeout**: 30 seconds
- **Max Notes/Day**: 100 (configurable)
- **Max Concurrent Users**: 10 (configurable)

## Development

### Code Style

This project follows:
- **PEP 8** for Python code style
- **PEP 257** for docstrings
- Type hints for function parameters and returns

### Adding Tests

Tests should be added to the `tests/` directory:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Logging

All important actions are logged to:
- **Console**: INFO level and above
- **File** (`logs/app.log`): All levels including DEBUG

To view logs:
```bash
# Tail the log file
tail -f logs/app.log
```

## Troubleshooting

### API Key Not Working

1. Verify your API key is correct in `.env`
2. Check xAI API status: https://status.x.ai
3. View logs in `logs/app.log` for error details

### Database Issues

```bash
# If database gets corrupted, restore from backup:
cp data/backups/notes_backup_YYYYMMDD_HHMMSS.db data/notes.db
```

### Application Not Starting

1. Ensure Python 3.9+ is installed: `python --version`
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Check logs in `logs/app.log`

## Roadmap

### Phase 1: MVP (Current)
- ✅ Core note input and processing
- ✅ Approval workflow
- ✅ Daily and categorized views
- ✅ Database with backups
- ✅ Basic logging

### Phase 2: Enhancements (Next)
- ⬜ Unit and integration tests
- ⬜ User authentication system
- ⬜ Enhanced statistics dashboard
- ⬜ Search functionality
- ⬜ Note editing after approval
- ⬜ Bulk operations

### Phase 3: Advanced Features
- ⬜ Multi-user collaboration
- ⬜ Note versioning
- ⬜ Advanced analytics
- ⬜ API rate limit monitoring
- ⬜ Automated daily backups
- ⬜ Email notifications

## Deployment

### Streamlit Cloud

**Quick Deploy:**
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository and select `app.py`
4. Add your `XAI_API_KEY` in the Secrets section
5. Deploy!

**📖 Full Deployment Guide:** See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete instructions, troubleshooting, and best practices.

### Local Production

```bash
# Run on specific port
streamlit run app.py --server.port 8080

# Run in headless mode
streamlit run app.py --server.headless true
```

### Docker (Optional)

Coming soon - Docker configuration for containerized deployment.

## Support

For issues, questions, or contributions:
1. Check the logs: `logs/app.log`
2. Review this README
3. Create an issue in the project repository

## License

[Add your license here]

## Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Powered by [xAI Grok API](https://x.ai)
- Inspired by project management best practices

---

**Version**: 1.0.0
**Last Updated**: 2025-10-24
**Author**: [Your Name]
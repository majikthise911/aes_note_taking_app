# Streamlit Notes App Specification (Optimized)
**Date**: 2025-10-22  
**Purpose**: To create a web-based Streamlit application for daily project note-taking, with automatic cleanup and categorization via the xAI GPT API, user approval of cleaned notes, and two views: a daily chronological view and a categorized view based on predefined project categories. The app ensures scalability, security, and usability for project managers, with robust testing and maintainability.

## 1. Executive Snapshot
This Streamlit app enables project managers to input daily notes, which are cleaned and categorized by the xAI GPT API. Users review and approve cleaned notes, which are stored in a SQLite database and displayed in two views: a Daily View (chronological by date) and a Categorized View (organized under predefined categories from the "Crescent / Felix PV — Living Project Status Log"). The app supports up to 100 notes/day and 10 concurrent users, with pagination, authentication, encryption, and comprehensive testing to ensure reliability and performance. A phased roadmap delivers a production-ready app in 7-9 weeks.

## 2. Key Features & Requirements
- **Note Input**:  
  - Users input raw notes via a Streamlit text area.  
  - A "Submit" button sends notes to the xAI GPT API for processing.  
  - Input validation prevents empty or malformed submissions.  
- **Note Cleanup via GPT API**:  
  - Notes sent to the xAI API (`https://x.ai/api`) with a prompt to clean grammar, structure, and clarity, and categorize under predefined categories.  
  - API returns JSON with fields: `cleaned_text`, `category`, `date` (YYYY-MM-DD), `timestamp` (HH:MM:SS).  
  - Retry logic (3 attempts, exponential backoff: 1s, 2s, 4s) handles API failures.  
  - Local caching stores cleaned notes if API is unavailable.  
- **User Approval**:  
  - Displays raw vs. cleaned notes side-by-side with proposed category.  
  - Approval form includes "Approve," "Reject," and "Edit" options (edit allows manual text/category changes).  
  - Approved notes are stored; rejected notes can be edited and resubmitted.  
  - Success/error notifications (`st.success`, `st.error`) confirm actions.  
- **Daily View**:  
  - Displays notes chronologically by date, with timestamps, in collapsible sections (`st.expander`).  
  - Pagination limits to 50 notes/page for performance.  
  - Filterable by date range (`st.date_input`).  
- **Categorized View**:  
  - Groups approved notes by predefined categories, displaying dates/timestamps.  
  - Pagination (50 notes/page) and category/date range filters.  
  - Uses `pandas` and `st.dataframe` for tabular display.  
- **Data Storage**:  
  - SQLite database with `notes` table: `id`, `raw_text`, `cleaned_text`, `category`, `date`, `timestamp`, `approval_status`.  
  - AES-256 encryption for stored notes.  
  - Daily backups to a secondary file.  
  - Indexes on `date` and `category` for query performance.  
- **User Interface**:  
  - Streamlit UI with tabs: Note Input, Daily View, Categorized View.  
  - Theme toggle (dark/light mode) via Streamlit config.  
  - Responsive design for desktop; mobile compatibility tested.  
  - Custom CSS for consistent fonts, spacing, and readability.  
- **Authentication**:  
  - Basic user authentication via `streamlit-authenticator` for multi-user support (up to 10 users).  
  - Role-based access: project managers (full access), developers (read-only for logs).  
- **Error Handling**:  
  - Handles API failures (rate limits, downtime) with retries and cached responses.  
  - User-friendly error messages for invalid inputs or API issues.  
- **Logging & Monitoring**:  
  - Python `logging` module tracks API calls, database operations, and user actions.  
  - Logs stored in a separate SQLite table for debugging.  
- **Performance**:  
  - Load time <2s for 1000 notes with pagination.  
  - Supports 100 notes/day and 10 concurrent users.  
- **Stakeholders**:  
  - **Primary Users**: Project managers needing efficient note organization.  
  - **Secondary Users**: Developers maintaining the app.  
  - **Needs**: Fast note input (<5s submission), 95% categorization accuracy, intuitive UI, secure data storage.  

## 3. Technical Components
- **Frontend**:  
  - **Streamlit**: UI framework with `st.text_area`, `st.form`, `st.tabs`, `st.expander`, `st.dataframe`, `st.date_input`.  
  - **CSS**: Custom styles via `st.markdown` for fonts, spacing, and theme toggle.  
- **Backend**:  
  - **Python 3.9+**: Core logic for API calls, data processing, and database interactions.  
  - **xAI GPT API**: Integrate via `requests` with JSON input/output.  
  - **SQLite**: Lightweight database with AES-256 encryption and daily backups.  
  - **Logging**: Python `logging` module for API, database, and user action logs.  
- **External Dependencies**:  
  - `streamlit==1.25.0`: UI framework.  
  - `requests==2.31.0`: API calls.  
  - `sqlite3`: Standard Python library for database. (Version not specified as it's included in Python 3.9+.)  
  - `python-dotenv==1.0.0`: Secure API key storage.  
  - `pandas==2.0.3`: Data manipulation for views.  
  - `streamlit-authenticator==0.2.3`: User authentication.  
  - `pycryptodome==3.18.0`: AES-256 encryption for notes.  
- **Code Standards**:  
  - PEP 8 for code style, PEP 257 for docstrings.  
  - Comprehensive docstrings and inline comments for all functions.  
- **Hosting**:  
  - Deploy on Streamlit Cloud (Enterprise) for production or AWS EC2 as fallback.  
  - Monitor performance via Streamlit logs and custom logging table.  

## 4. Data Flow
1. **Input**: User logs in, enters raw notes in text area, submits via form.  
2. **API Call**: Notes sent to xAI API with prompt for cleanup and categorization. Response validated against JSON schema: `{ "cleaned_text": str, "category": str, "date": str, "timestamp": str }`. Retries on failure; caches response if unavailable.  
3. **Approval**: Streamlit displays raw vs. cleaned notes with edit form. User approves, rejects, or edits (text/category). Notifications confirm actions.  
4. **Storage**: Approved notes encrypted and saved to SQLite with `approval_status=approved`. Rejected notes marked `rejected` for resubmission.  
5. **Display**:  
   - **Daily View**: Query SQLite (`SELECT * FROM notes WHERE approval_status='approved' ORDER BY date, timestamp LIMIT 50 OFFSET X`), paginated, filtered by date.  
   - **Categorized View**: Query SQLite (`SELECT * FROM notes WHERE approval_status='approved' AND category=? ORDER BY date, timestamp LIMIT 50 OFFSET X`), paginated, filtered by category/date.  
6. **Logging**: Log API calls, database operations, and user actions (e.g., login, submit, approve) to SQLite `logs` table.  

## 5. Predefined Categories
From "Crescent / Felix PV — Living Project Status Log":  
- General  
- Development/Reliance Material  
- GIS updates  
- Interconnection  
- Land  
- Facility location  
- Environmental/Biological Cultural  
- Schedule  
- Breakers  
- MPT  
- Modules  
- Owner’s Engineer  
- 30% Package  
- 60% Package  
- Geotech investigation  
- Structural  
- Civil  
- Electrical  
- Substation  
- Construction Milestones  
- Pricing  
- Risk Register  
- Permanent Utilities  
- Contracting  
- LNTP  
- BOP-EPC  
- PWC  
- Action Items  

## 6. Development Roadmap
### Phase 1: Setup & Core Functionality (2-3 weeks)  
- **Tasks**:  
  - Set up Streamlit project (`requirements.txt`, Python 3.9+).  
  - Configure SQLite with `notes` and `logs` tables; add indexes on `date`, `category`.  
  - Implement note input form with validation (`st.form`, `st.text_area`).  
  - Integrate xAI GPT API with `requests`, retry logic (3 attempts, exponential backoff: 1s, 2s, 4s), and caching.  
  - Build approval form with raw/cleaned comparison, edit option, and notifications.  
  - Set up `streamlit-authenticator` for user login (support 10 users).  
  - Configure `logging` module for API, database, and user actions.  
  - Implement AES-256 encryption for stored notes using `pycryptodome`.  
- **Deliverables**:  
  - Streamlit app with note input, API integration, approval workflow, authentication, and logging.  
  - SQLite database with encrypted notes and indexes.  
- **Acceptance Criteria**:  
  - Submit 10 notes, receive cleaned JSON within 5s (95% success rate).  
  - Approve/reject/edit notes with notifications.  
  - Login supports 10 users with role-based access.  
- **Risks**: API rate limits or inconsistent JSON. **Mitigation**: Strict JSON schema validation, retry logic, caching.  

### Phase 2: Views Implementation (2 weeks)  
- **Tasks**:  
  - Build Daily View: Query SQLite, display paginated notes (50/page) in `st.expander`.  
  - Build Categorized View: Group notes by category, paginated, using `pandas` and `st.dataframe`.  
  - Add date range filters (`st.date_input`) and category filters (`st.selectbox`).  
  - Implement theme toggle (dark/light mode) via Streamlit config.  
  - Apply custom CSS for fonts (e.g., Roboto), spacing, and readability.  
  - Optimize queries with indexes; benchmark load time (<2s for 1000 notes).  
- **Deliverables**:  
  - Functional Daily and Categorized views with pagination and filters.  
  - Polished UI with theme toggle and responsive design.  
- **Acceptance Criteria**:  
  - Views load 1000 notes in <2s with pagination.  
  - Filters return accurate results in <1s.  
  - UI renders correctly on desktop (mobile optional).  
- **Risks**: Slow view rendering with large datasets. **Mitigation**: Pagination, query optimization.  

### Phase 3: Testing & Refinement (2 weeks)  
- **Tasks**:  
  - Write unit tests (`pytest`) for API calls, database queries, and UI components (>80% coverage).  
  - Run integration tests for end-to-end flow (input → API → storage → views).  
  - Stress test with 1000 notes/day, 10 concurrent users (<2s load time).  
  - Conduct usability tests across devices (desktop, mobile).  
  - Refine GPT prompt for 95% categorization accuracy (test with 100 sample notes).  
  - Add daily SQLite backups to secondary file.  
  - Gather user feedback; iterate on UI (e.g., adjust filters, notifications).  
- **Deliverables**:  
  - Bug-free app with test suite (unit, integration, stress, usability).  
  - Refined GPT prompt and UI based on feedback.  
  - Daily database backups implemented.  
- **Acceptance Criteria**:  
  - Test coverage >80%.  
  - 95% categorization accuracy on sample notes.  
  - App handles 1000 notes/day, 10 users without errors.  
- **Risks**: GPT mis-categorization, UI usability issues. **Mitigation**: Manual category override, user feedback iteration.  

### Phase 4: Deployment & Documentation (1-2 weeks)  
- **Tasks**:  
  - Deploy on Streamlit Cloud (Enterprise) or AWS EC2.  
  - Configure daily backups and encryption for SQLite.  
  - Write user guide: Note input, approval, view navigation.  
  - Write developer README: Setup, API usage, PEP 8/257, error handling (API codes, database errors).  
  - Monitor performance via Streamlit logs and SQLite `logs` table.  
- **Deliverables**:  
  - Live app accessible to 10 users.  
  - User and developer documentation (README with PEP 8/257 compliance).  
  - Secure deployment with backups and monitoring.  
- **Acceptance Criteria**:  
  - App uptime >99.9% during first week.  
  - Documentation enables setup in <30 min.  
  - Logs capture all API/database/user actions.  
- **Risks**: Deployment issues (e.g., Streamlit Cloud limits). **Mitigation**: AWS EC2 fallback, monitor logs.  

## 7. Assumptions
- **Usage**: 100 notes/day, 10 concurrent users (project managers, developers).  
- **xAI API**: Available at `https://x.ai/api` with sufficient quota (1000 calls/day). Returns consistent JSON.  
- **Categories**: Fixed to 27 predefined categories from the provided document; no custom categories.  
- **Database**: SQLite sufficient for 100,000 notes/year; PostgreSQL fallback if performance degrades.  
- **Authentication**: Required for multi-user access; single-user mode optional.  
- **Users**: Familiar with web-based interfaces; minimal training needed.  

## 8. Risks & Mitigations
- **High Risk**: API downtime/rate limits (Probability: Medium, Impact: App failure, ~$500/day downtime cost).  
  - **Mitigation**: Retry logic (3 attempts), cache cleaned notes, notify users of failures.  
- **Medium Risk**: SQLite performance with 100,000+ notes (Probability: Low, Impact: Slow UI, ~$200/day user productivity loss).  
  - **Mitigation**: Pagination (50 notes/page), indexes, PostgreSQL fallback plan.  
- **Medium Risk**: Unauthorized access to notes (Probability: Medium, Impact: Data breach, ~$1000/incident).  
  - **Mitigation**: `streamlit-authenticator`, AES-256 encryption.  
- **Low Risk**: GPT mis-categorization (Probability: Medium, Impact: User rework, ~$50/day).  
  - **Mitigation**: Manual category edits in approval form, refine prompt.  
- **Low Risk**: UI usability issues (Probability: Low, Impact: User frustration, ~$100/day).  
  - **Mitigation**: Usability testing, feedback iteration, notifications.  

## 9. Source Register
- **Tier-3**: IEEE-830 (Software Requirements Specifications, 1998) for structure and completeness.  
- **Tier-5**: Streamlit documentation (`https://docs.streamlit.io`, accessed 2025-10-22) for UI components.  
- **Tier-5**: Python PEP 8/257 for code style and documentation.  
- **Tier-5**: xAI API documentation (`https://x.ai/api`, assumed for integration details).  
- **User-Provided**: "Crescent / Felix PV — Living Project Status Log" for categories (2025-08-11).  

## 10. Remaining Unknowns
- Exact xAI API error codes and rate limits. **Recommendation**: Verify via `https://x.ai/api`.  
- User preferences for UI styling (e.g., colors, fonts). **Recommendation**: Conduct stakeholder interview.  
- Long-term note volume growth (>100,000 notes/year). **Recommendation**: Monitor performance post-deployment; plan PostgreSQL migration if needed.  

## 11. Sample GPT Prompt
```
Clean the following raw notes for grammar, structure, and clarity. Categorize each note under one of the following predefined categories: [General, Development/Reliance Material, GIS updates, Interconnection, Land, Facility location, Environmental/Biological Cultural, Schedule, Breakers, MPT, Modules, Owner’s Engineer, 30% Package, 60% Package, Geotech investigation, Structural, Civil, Electrical, Substation, Construction Milestones, Pricing, Risk Register, Permanent Utilities, Contracting, LNTP, BOP-EPC, PWC, Action Items]. Return the output in JSON format with fields: cleaned_text, category, date (YYYY-MM-DD), timestamp (HH:MM:SS). Ensure the meaning is preserved and JSON is valid.

Raw Notes: [user_input]

Example Output:
[
  {
    "cleaned_text": "Reviewed Primoris bid; cost at 61.2 cents/W.",
    "category": "Pricing",
    "date": "2025-10-22",
    "timestamp": "12:30:00"
  },
  ...
]
```

## 12. Sample Database Schema
```sql
CREATE TABLE notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  raw_text TEXT NOT NULL,
  cleaned_text TEXT,
  category TEXT,
  date TEXT,
  timestamp TEXT,
  approval_status TEXT CHECK(approval_status IN ('pending', 'approved', 'rejected')),
  INDEX idx_date (date),
  INDEX idx_category (category)
);

CREATE TABLE logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT,
  level TEXT,
  message TEXT,
  user_id TEXT
);
```

## 13. Acceptance Criteria
- **Note Input**: Submit 100 notes/day, processed in <5s (95% success rate).  
- **API Integration**: Handles 1000 API calls/day with <1% failure rate (retries/caching).  
- **Views**: Load 1000 notes in <2s with pagination; filters return results in <1s.  
- **Categorization**: 95% accuracy on 100 sample notes; manual override available.  
- **Security**: No unauthorized access; notes encrypted with AES-256.  
- **Reliability**: App uptime >99.9%; daily backups functional.  
- **Usability**: UI intuitive, confirmed by 5/5 user feedback score in testing.
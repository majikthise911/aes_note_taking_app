# Pre-Deployment Checklist

Use this checklist before deploying to Streamlit Cloud.

## ✅ Code Readiness

- [ ] All code changes tested locally
- [ ] App runs without errors: `streamlit run app.py`
- [ ] All features work as expected
- [ ] No sensitive data in code (API keys, passwords, etc.)

## ✅ Files to Commit

- [ ] `.streamlit/config.toml` - Streamlit configuration
- [ ] `requirements.txt` - All dependencies listed
- [ ] `DEPLOYMENT.md` - Deployment documentation
- [ ] `.gitignore` - Excludes `.env` and `secrets.toml`
- [ ] `README.md` - Updated with deployment info

## ✅ Files to EXCLUDE (already in .gitignore)

- [ ] `.env` - Contains secrets (local only)
- [ ] `.streamlit/secrets.toml` - Contains secrets (local only)
- [ ] `data/` - Database files (generated at runtime)
- [ ] `logs/` - Log files (generated at runtime)
- [ ] `__pycache__/` - Python cache files

## ✅ GitHub Setup

- [ ] Code pushed to GitHub
- [ ] Repository is public OR you have Streamlit Cloud paid plan
- [ ] Main branch is `main` or `master`
- [ ] `app.py` is in the root directory

## ✅ Streamlit Cloud Setup

- [ ] Streamlit Cloud account created
- [ ] GitHub account connected to Streamlit Cloud
- [ ] xAI API key ready to add to secrets

## ✅ Secrets Configuration

Prepare these secrets for Streamlit Cloud:

```toml
XAI_API_KEY = "your_actual_api_key"
XAI_API_URL = "https://api.x.ai/v1/chat/completions"
XAI_MODEL = "grok-4-fast-reasoning"
AUTH_ENABLED = "False"
LOG_LEVEL = "INFO"
```

## ✅ Post-Deployment Testing

After deployment, test:

- [ ] App loads without errors
- [ ] New note creation works
- [ ] AI processing works (check xAI API key)
- [ ] Approval workflow works
- [ ] Pagination works in approval view
- [ ] Daily view shows notes
- [ ] Category view and CSV export work
- [ ] Sidebar statistics display correctly

## 🚀 Ready to Deploy!

If all boxes are checked, you're ready to deploy!

Follow the steps in [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

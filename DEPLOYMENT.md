# Deployment Guide - Streamlit Cloud

This guide covers deploying the Project Notes Manager to Streamlit Cloud.

## Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Streamlit Cloud Account** - Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **xAI API Key** - Get one from [x.ai](https://x.ai)

## Pre-Deployment Checklist

### 1. Commit Your Changes

```bash
# Add all changes
git add .

# Commit with a message
git commit -m "Prepare app for Streamlit Cloud deployment"

# Push to GitHub
git push origin main
```

### 2. Verify Files Are Ready

Ensure these files exist:
- ✅ `requirements.txt` - Python dependencies
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `.gitignore` - Excludes `.env` and `secrets.toml`
- ✅ `app.py` - Main application entry point

## Deployment Steps

### Step 1: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Connect your GitHub account if not already connected
4. Select:
   - **Repository**: `your-username/aes_note_taking_app`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Click **"Advanced settings"** before deploying

### Step 2: Configure Secrets

In the Advanced settings, add your secrets in the **Secrets** section:

```toml
# Streamlit secrets format
XAI_API_KEY = "your_actual_xai_api_key_here"
XAI_API_URL = "https://api.x.ai/v1/chat/completions"
XAI_MODEL = "grok-4-fast-reasoning"

# Authentication (optional)
AUTH_ENABLED = "False"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "changeme"

# Logging
LOG_LEVEL = "INFO"
```

**Important:**
- Replace `your_actual_xai_api_key_here` with your real API key
- Never commit secrets to GitHub
- Keep AUTH_ENABLED = "False" unless you want to enable authentication

### Step 3: Deploy

1. Click **"Deploy!"**
2. Wait 2-5 minutes for the app to build and deploy
3. Your app will be live at `https://your-app-name.streamlit.app`

## Post-Deployment

### Verify Deployment

1. **Test New Note Creation**
   - Go to "📝 New Note" tab
   - Enter a test note
   - Verify AI processes it correctly

2. **Test Approval Workflow**
   - Go to "✅ Approve Notes" tab
   - Verify pagination works (if you have 50+ notes)
   - Approve/reject a note

3. **Test Views**
   - Check "📅 Daily View" shows approved notes
   - Check "🗂️ By Category" allows filtering and CSV export

4. **Check Logs**
   - Streamlit Cloud provides logs in the app menu
   - Look for any errors or warnings

### Monitor Usage

- **Logs**: View in Streamlit Cloud dashboard
- **API Usage**: Monitor xAI API calls and costs at x.ai
- **App Analytics**: Available in Streamlit Cloud dashboard

## Troubleshooting

### App Won't Start

**Error**: `ModuleNotFoundError`
- **Solution**: Check `requirements.txt` has all dependencies

**Error**: `XAI_API_KEY not configured`
- **Solution**: Add `XAI_API_KEY` to Streamlit secrets (see Step 2)

### Database Issues

**Issue**: Data doesn't persist between sessions
- **Cause**: Streamlit Cloud ephemeral storage
- **Solution**:
  - For production, consider using:
    - Streamlit Cloud's built-in SQLite persistence
    - External database (PostgreSQL, MongoDB)
    - See [Streamlit docs on data persistence](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app#app-dependencies)

**Issue**: Database resets on app reboot
- **Expected behavior**: SQLite database in `/data` directory persists across sessions but may reset on app updates
- **Recommendation**: Implement periodic backups or use external database for production

### Performance Issues

**Issue**: App is slow
- Check API response times in logs
- Consider caching frequent queries
- Review pagination settings in `config/settings.py`

**Issue**: API rate limits
- Monitor API usage
- Implement rate limiting in code if needed
- Consider caching API responses

## Configuration Options

### Environment Variables (Streamlit Secrets)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `XAI_API_KEY` | ✅ Yes | - | Your xAI API key |
| `XAI_API_URL` | No | `https://api.x.ai/v1/chat/completions` | xAI API endpoint |
| `XAI_MODEL` | No | `grok-4-fast-reasoning` | xAI model to use |
| `AUTH_ENABLED` | No | `False` | Enable authentication |
| `ADMIN_USERNAME` | No | `admin` | Admin username (if auth enabled) |
| `ADMIN_PASSWORD` | No | `changeme` | Admin password (if auth enabled) |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### App Settings

Modify in `config/settings.py`:
- `NOTES_PER_PAGE` - Notes per page (default: 50)
- `API_MAX_RETRIES` - API retry attempts (default: 3)
- `API_TIMEOUT` - API request timeout in seconds (default: 30)

### Categories

Modify in `config/categories.py`:
- Add/remove project categories
- Update category validation

## Updating Your Deployed App

```bash
# Make changes locally
# Test locally: streamlit run app.py

# Commit changes
git add .
git commit -m "Update app with new features"

# Push to GitHub
git push origin main
```

Streamlit Cloud will automatically detect the changes and redeploy your app within 1-2 minutes.

## Security Best Practices

1. **Never commit secrets** - Use Streamlit Cloud secrets management
2. **Keep dependencies updated** - Regularly update `requirements.txt`
3. **Review logs regularly** - Check for errors or unusual activity
4. **Enable authentication** - Set `AUTH_ENABLED=True` for production use
5. **Monitor API usage** - Track xAI API costs and usage

## Cost Considerations

### Streamlit Cloud
- **Free Tier**: 1 app, public repos only
- **Paid Tiers**: Multiple apps, private repos, more resources
- See [Streamlit pricing](https://streamlit.io/cloud)

### xAI API
- Pay per API call
- Monitor usage at [x.ai](https://x.ai)
- Consider implementing usage limits

## Support

- **Streamlit Cloud Issues**: [Streamlit Community Forum](https://discuss.streamlit.io)
- **xAI API Issues**: [xAI Documentation](https://docs.x.ai)
- **App Issues**: Check `logs/app.log` or Streamlit Cloud logs

## Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Streamlit Cloud Deployment Guide](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [xAI API Documentation](https://docs.x.ai)
- [GitHub Actions for CI/CD](https://docs.github.com/en/actions) (optional)

---

**Version**: 1.0.0
**Last Updated**: 2025-10-29

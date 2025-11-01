# Women's Safety & Support Hub

A Flask web application for documenting safety incidents with AI-powered summary generation and anonymous community support.

## Features

✅ **Multi-step Incident Report Form**
- Guided questionnaire with visual icons
- Evidence file upload support
- Date/time tracking
- Multiple impact categories

✅ **AI-Generated Summaries**
- Uses Google Gemini Pro API
- Professional, empathetic tone
- Suitable for official documentation

✅ **Community Support Wall**
- Anonymous posting
- Support reactions (hearts)
- Comment system for peer support

## What Was Fixed

1. **Replaced Google SDK with REST API**: Changed from `google.generativeai` package to direct REST API calls
2. **Configured Gemini API Key**: Integrated your API key: `AIzaSyCWa3C1wZ0cG1bSdEqFAdHs826i34HY5k0`
3. **Fixed App Structure**: Corrected the Flask app factory pattern
4. **Updated Dependencies**: Removed unnecessary packages

## Quick Start

### 1. Install Dependencies (Already Done)
```powershell
cd "c:\Users\abhi1\OneDrive\Desktop\women-safety\women-safety-app"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Start the Server
```powershell
& "c:\Users\abhi1\OneDrive\Desktop\women-safety\women-safety-app\.venv\Scripts\python.exe" "c:\Users\abhi1\OneDrive\Desktop\women-safety\women-safety-app\app.py"
```

### 3. Access the App
Open your browser and visit: **http://127.0.0.1:5000**

## Server Status

✅ **Currently Running** on http://127.0.0.1:5000
- Debug mode: ON
- Debugger PIN: 502-808-890

## Project Structure

```
women-safety-app/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes.py            # All routes and Gemini API integration
│   ├── templates/
│   │   ├── base.html
│   │   ├── incident_report.html
│   │   ├── report_summary.html
│   │   └── community_support.html
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/dynamic_form.js
│   └── uploads/evidence/    # File upload directory
├── app.py                   # Application entry point
├── config.py                # Configuration
└── requirements.txt         # Python dependencies
```

## Usage Guide

### 1. File an Incident Report
1. Visit http://127.0.0.1:5000
2. Answer the multi-step questionnaire:
   - Who was involved?
   - What type of incident?
   - Where did it happen?
   - Impact on you
   - Date and time
   - First occurrence?
3. Optionally upload evidence files
4. Click "Generate Report"

### 2. AI Summary Generation
- The Gemini AI will create a professional summary
- Takes 5-10 seconds to generate
- Summary is empathetic and factual

### 3. Share Anonymously (Optional)
- Post your summary to the community wall
- Remain completely anonymous
- Receive support from others

### 4. Community Wall
- View other anonymous stories
- Send support with hearts ❤️
- Add supportive comments
- All interactions are anonymous

## API Configuration

The Gemini API is configured in `app/routes.py`:
```python
GEMINI_API_KEY = 'AIzaSyCWa3C1wZ0cG1bSdEqFAdHs826i34HY5k0'
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'
```

## Security Notes

⚠️ **For Production Deployment:**
1. Move API key to environment variables
2. Use HTTPS
3. Add rate limiting
4. Implement proper database storage
5. Add user authentication (if needed)
6. Change SECRET_KEY in config

## Troubleshooting

### Server Won't Start
```powershell
# Check if port 5000 is already in use
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process
```

### API Errors
- Check your internet connection
- Verify the API key is valid
- Check Gemini API quota limits

### File Upload Issues
- Ensure `app/uploads/evidence/` directory exists
- Check file size (max 16MB)
- Allowed formats: png, jpg, jpeg, gif, mp3, wav, m4a, mp4, mov, pdf

## Stop the Server

Press `Ctrl+C` in the terminal running the Flask app.

## Next Steps

- [ ] Add database integration (SQLite/PostgreSQL)
- [ ] Implement persistent storage for posts
- [ ] Add export to PDF feature
- [ ] Implement search/filter on community wall
- [ ] Add email notifications (optional)
- [ ] Deploy to cloud platform

## Real-time SOS alerts (SMS + WhatsApp)

The SOS Center can notify your emergency contacts immediately:

- WhatsApp: On SOS activation, a modal opens with a Share button (choose multiple recipients) and per-contact WhatsApp buttons. This requires you to tap to send (WhatsApp does not allow fully automatic sending without the Business API).
- SMS: The server can send real SMS automatically using Twilio if configured. If not configured, it logs a mock send to app/uploads/sos/logs/sms_log.json.

Enable real SMS via Twilio (Windows PowerShell):

```powershell
$env:TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:TWILIO_AUTH_TOKEN = "your_auth_token"
$env:TWILIO_FROM_NUMBER = "+1XXXXXXXXXX"  # Your Twilio SMS-enabled number in E.164 format
```

Then install dependencies and run the app:

```powershell
cd "c:\Users\abhi1\OneDrive\Desktop\women-safety\women-safety-app"
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe app.py
```

Notes:
- Store contact phone numbers in E.164 format (e.g., +9198XXXXXXXX) for best SMS delivery.
- WhatsApp Business Cloud API requires Facebook Business verification and approved templates; not enabled by default in this project.

## Support Resources (Placeholder)

- National Helpline: 123-456
- Local Support Center: 987-654
- Emergency Services: 911

---

**Built with:** Flask, Tailwind CSS, Gemini AI
**License:** MIT
**Last Updated:** November 1, 2025

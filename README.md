# 🏦 Gringotts – Women's Safety & Support Hub

**Gringotts** is a comprehensive Flask-based safety application with AI assistance, safe route planning, instant SOS alerts, incident reporting, and an anonymous community support wall. It runs locally with HTTPS to enable secure browser permissions (location, microphone, camera, notifications).

## ✨ Key Features

### 🚨 **SOS Center**
- One-tap emergency alerts with live GPS tracking
- Automatic SMS notifications to emergency contacts
- WhatsApp alert integration with tracking links
- Voice/video recording during emergencies
- Real-time location broadcasting every 60 seconds

### 🗺️ **Safe Routes**
- AI-powered route optimization based on:
  - Crime density analysis (260 crime records)
  - Street lighting coverage (1,144 lighting points)
  - Population density (187 data points)
- Interactive map with safety scores
- Multiple route options with detailed metrics

### 📝 **Incident Reporting**
- Step-by-step guided questionnaire
- AI-generated professional summaries (Gemini)
- Evidence upload (photos, audio, video, documents)
- Anonymous or identified reporting options
- Export reports for official documentation

### 🤝 **Community Support**
- Anonymous story sharing
- Peer support with reactions and comments
- AI-powered emotional support chat
- Safe space for sharing experiences

### 🎭 **Fake Call Feature**
- AI-powered conversational fake calls (Gemini)
- Voice recognition for natural responses
- Escape dangerous situations discreetly
- Customizable caller names

### 🔐 **Privacy & Security**
- HTTPS encryption (self-signed certificate for local dev)
- Anonymous posting options
- Secure data storage
- No personal data exposure without consent

---

## 🚀 Quick Start Guide (Windows)

### Step 1: Clone the Repository
```powershell
# Clone from GitHub
git clone https://github.com/abhiraamadiga/women-safety-app.git
cd women-safety-app\women-safety-app
```

### Step 2: Create Virtual Environment
```powershell
# Create a new virtual environment
python -m venv .venv

# Activate the virtual environment
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 3: Install Dependencies
```powershell
# Install all required packages
pip install -r requirements.txt
```

**Required packages will be installed:**
- Flask (web framework)
- Flask-SQLAlchemy (database ORM)
- Flask-CORS (cross-origin requests)
- pandas & numpy (data analysis for safe routes)
- requests (API calls to Gemini, SMS providers)
- python-dotenv (environment variable management)
- werkzeug (file uploads & security)
- gevent (HTTPS server support)

### Step 4: Configure Environment Variables
Create a file named `.env` in the `women-safety-app` folder:

```env
# ===== REQUIRED: Google Gemini AI =====
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_API_VERSION=v1

# ===== OPTIONAL: SMS Providers (for automatic SOS alerts) =====
# Fast2SMS (Indian SMS service - requires 10-digit numbers)
FAST2SMS_API_KEY=your_fast2sms_key_here

# OR Twilio (International SMS - requires E.164 format: +919876543210)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here

# ===== Flask Configuration =====
SECRET_KEY=change-this-to-a-random-secret-key-in-production
```

**🔑 Get Your Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it in `.env`

### Step 5: Generate SSL Certificate (First Time Only)
The app needs HTTPS for browser permissions. Generate a self-signed certificate:

```powershell
# The cert.pem and key.pem files should already be in the repo
# If missing, you can generate them:
# pip install pyopenssl
# python -c "from OpenSSL import crypto; k = crypto.PKey(); k.generate_key(crypto.TYPE_RSA, 2048); c = crypto.X509(); c.get_subject().CN = 'localhost'; c.set_serial_number(1000); c.gmtime_adj_notBefore(0); c.gmtime_adj_notAfter(365*24*60*60); c.set_issuer(c.get_subject()); c.set_pubkey(k); c.sign(k, 'sha256'); open('cert.pem', 'wb').write(crypto.dump_certificate(crypto.FILETYPE_PEM, c)); open('key.pem', 'wb').write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))"
```

### Step 6: Start the Server
```powershell
# Make sure virtual environment is activated
& .\.venv\Scripts\Activate.ps1

# Start HTTPS server on port 5443
python app.py --https --https-port 5443
```

You should see:
```
============================================================
🚀 Women's Safety App - FULL APPLICATION
============================================================
📊 Crime data: 260 records
💡 Lighting data: 1144 points
👥 Population data: 187 points
...
🔐 Starting HTTPS server
   URL        : https://127.0.0.1:5443
```

### Step 7: Open in Browser
1. Open your browser and go to: **https://127.0.0.1:5443**
2. You'll see a security warning (normal for self-signed certificates)
3. Click "Advanced" → "Proceed to 127.0.0.1 (unsafe)" or similar
4. The onboarding screen will appear requesting permissions
5. Grant permissions for full functionality

### Step 8: Test the Application
```powershell
# Check server health
curl.exe -k https://127.0.0.1:5443/api/health

# Check Gemini AI status
curl.exe -k https://127.0.0.1:5443/api/ai-status
```

---

## 📱 Accessing from Mobile Device

To test on your phone (same WiFi network):

1. Find your PC's IP address:
```powershell
ipconfig
# Look for "IPv4 Address" under your active network adapter
# Example: 192.168.1.100
```

2. On your phone, visit: `https://YOUR_IP:5443`
   - Example: `https://192.168.1.100:5443`

3. Accept the certificate warning on mobile browser

4. Grant permissions when the onboarding modal appears

## Project Structure

```
women-safety-app/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes.py            # All routes (SOS, Chat, Safe Routes, etc.)
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

### 2. AI Summary & Chat
- The Gemini AI will create a professional summary
- Takes 5-10 seconds to generate
- Summary is empathetic and factual
- Chat: visit /support-chat or start AI Fake Call at /fake-call

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

Gemini configuration is read from environment variables via `.env` (no keys in code). See Quick Start step 2.

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
# Common fixes
# 1) Ensure venv is activated and deps are installed
& .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt

# 2) If port 5443 in use, kill previous Python processes
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process
```

### Gemini API Errors
- Verify GEMINI_API_KEY is set and valid
- Ensure `.env` is in the `women-safety-app` folder
- Confirm model/version: `GEMINI_MODEL=gemini-2.0-flash`, `GEMINI_API_VERSION=v1`

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

## SOS Alerts (SMS + WhatsApp)

The SOS Center can notify your emergency contacts immediately:

- WhatsApp: On SOS activation, a modal opens with a Share button (choose multiple recipients) and per-contact WhatsApp buttons. This requires you to tap to send (WhatsApp does not allow fully automatic sending without the Business API).
- SMS: The server can send real SMS automatically using Fast2SMS or Twilio if configured. If not configured, it logs a mock send to `app/uploads/sos/logs/sms_log.json`.

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
- For Twilio, store contact numbers in E.164 (e.g., +9198XXXXXXXX). For Fast2SMS, store 10-digit Indian numbers.
- If provider calls fail, the app still logs the message and shows it in the console and `sms_log.json` so you can send manually.
- WhatsApp Business Cloud API requires Facebook Business verification and approved templates; not enabled by default in this project.

## Support Resources (Placeholder)

- National Helpline: 123-456
- Local Support Center: 987-654
- Emergency Services: 911

---

**Built with:** Flask, Bootstrap, Leaflet, Gemini AI
**License:** MIT
**Last Updated:** November 2, 2025



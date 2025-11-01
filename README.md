# Women Safety App 🛡️

A comprehensive web application designed to enhance women's safety in Bangalore through intelligent route planning, incident reporting, and community support features.

## 🌟 Features

### 1. **Safe Route Planner**
- Real-time route optimization based on crime data
- Multiple route options with safety scores
- Integration with 260+ crime records
- 1,144+ lighting data points
- 187+ population density points
- Customizable preferences (well-lit streets, populated areas, main roads)

### 2. **User Authentication**
- Secure login/signup system
- Username-based profiles
- Privacy controls and consent management

### 3. **Incident Reporting**
- Anonymous or identified reporting
- Evidence upload (photos, audio, video)
- Location tagging
- AI-powered report analysis using Gemini API

### 4. **Community Support**
- Anonymous community posts
- Comment system
- Safe space for sharing experiences

### 5. **SOS Center**
- Emergency alert system
- Live location tracking
- Shake intensity detection
- Automatic recording
- Emergency contact notification

### 6. **Emergency Contacts**
- Quick access to emergency numbers
- Custom emergency contact management

### 7. **Fake Call Feature**
- Emergency escape mechanism
- Customizable caller details

## 🚀 Tech Stack

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Database
- **Pandas & NumPy** - Data analysis
- **Flask-CORS** - Cross-origin support

### Frontend
- **HTML5, CSS3, JavaScript**
- **Bootstrap 5** - UI framework
- **Leaflet.js** - Interactive maps
- **OpenStreetMap** - Map data

### APIs & Services
- **OSRM** - Route optimization
- **Nominatim** - Geocoding
- **Google Gemini API** - AI analysis

### Additional Features
- **Node.js Server** (Port 3000) - SOS features, recording uploads
- **Express.js** - API server
- **Multer** - File upload handling

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 14+
- Git

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd women-safety
```

2. **Set up Python environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Mac/Linux
```

3. **Install Python dependencies**
```bash
cd women-safety-app
pip install -r requirements.txt
```

4. **Install Node.js dependencies**
```bash
cd ..
npm install
```

5. **Create environment file**
```bash
# Create .env file in root directory
# Add your API keys:
GEMINI_API_KEY=your_api_key_here
```

## 🏃‍♀️ Running the Application

### Start the main Flask application:
```bash
cd women-safety-app
python app.py
```
The app will run on **http://127.0.0.1:5000**

### Start the Node.js SOS server:
```bash
node new_feature_server.js
```
The server will run on **http://localhost:3000**

## 📊 Data Files

The application uses CSV files for safety analysis:
- `bangalore_crimes.csv` - Crime incident data
- `bangalore_lighting.csv` - Street lighting information
- `bangalore_population.csv` - Population density data

Located in: `women-safety-app/app/data/`

## 🗂️ Project Structure

```
women-safety/
├── women-safety-app/           # Main Flask application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes.py           # Application routes
│   │   ├── models.py           # Database models
│   │   ├── auth_models.py      # User authentication models
│   │   ├── templates/          # HTML templates
│   │   ├── static/             # CSS, JS, images
│   │   └── data/               # CSV data files
│   ├── app.py                  # Main application file
│   ├── config.py               # Configuration
│   └── requirements.txt        # Python dependencies
├── new_feature_server.js       # Node.js SOS server
├── new_feature_index.html      # SOS frontend
├── package.json                # Node.js dependencies
└── README.md

```

## 🔐 Security Features

- Password hashing with Werkzeug
- Session management
- CSRF protection
- Secure file uploads
- Anonymous reporting options
- Data retention controls

## 🌈 Key Highlights

- **Crime-Aware Routing**: Analyzes historical crime data to suggest safer routes
- **Real-time Safety Scoring**: Each route receives a safety score (0-100)
- **Multiple Route Options**: Shows up to 7 alternative routes
- **Preference-Based**: Customize based on lighting, population, and road type
- **Community-Driven**: Anonymous reporting and support system

## 📱 Mobile Responsive

The application is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile devices

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is for educational and safety purposes.

## 👥 Support

For support or queries, please open an issue in the repository.

---

**Built with ❤️ for women's safety in Bangalore**

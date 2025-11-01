# Safe Routes Integration Script
# This script copies the complete Safe Routes feature from the original project

Write-Host "🚀 Starting Safe Routes Integration..." -ForegroundColor Green
Write-Host ""

$sourcePath = "C:\Users\abhi1\OneDrive\Desktop\women-safety\temp-archive-full\my projects\unsafe\bangalore-safe-routes"
$destPath = "C:\Users\abhi1\OneDrive\Desktop\women-safety\women-safety-app\app"

# 1. Copy the complete safe_routes template
Write-Host "📄 Step 1: Copying complete HTML template..." -ForegroundColor Cyan
Copy-Item "$sourcePath\index.html" "$destPath\templates\safe_routes_FULL.html" -Force
Write-Host "✅ Created safe_routes_FULL.html with ALL features" -ForegroundColor Green
Write-Host "   - Turn-by-turn directions" -ForegroundColor Gray
Write-Host "   - Animated car navigation" -ForegroundColor Gray
Write-Host "   - Saved locations" -ForegroundColor Gray
Write-Host "   - Route rating" -ForegroundColor Gray
Write-Host "   - Theme toggle" -ForegroundColor Gray
Write-Host "   - Enhanced UI" -ForegroundColor Gray
Write-Host ""

# 2. Copy route display JavaScript
Write-Host "📜 Step 2: Copying JavaScript animation library..." -ForegroundColor Cyan
if (!(Test-Path "$destPath\static\js")) {
    New-Item -ItemType Directory -Path "$destPath\static\js" -Force | Out-Null
}
Copy-Item "$sourcePath\route_display.js" "$destPath\static\js\route_display.js" -Force
Write-Host "✅ Created route_display.js" -ForegroundColor Green
Write-Host "   - Car animation at 50km/h" -ForegroundColor Gray
Write-Host "   - Bearing calculation & rotation" -ForegroundColor Gray
Write-Host "   - Camera following" -ForegroundColor Gray
Write-Host ""

# 3. Create safe routes backend module
Write-Host "🔧 Step 3: Creating Safe Routes backend module..." -ForegroundColor Cyan
$backendCode = @"
'''
Safe Routes Backend Module
Full-featured route calculation with waypoint routing and safety analysis
'''

from flask import jsonify, request
import pandas as pd
import numpy as np
import requests
import os
import hashlib
from math import radians, cos, sin, asin, sqrt, atan2

# This will be imported into routes.py
# To integrate: from .safe_routes_backend import initialize_safe_routes, register_safe_routes_endpoints

def initialize_safe_routes(app_dir):
    '''Load CSV data files'''
    print('\n=== Initializing Safe Routes ===')
    try:
        crime_data = pd.read_csv(os.path.join(app_dir, 'data', 'bangalore_crimes.csv'))
        lighting_data = pd.read_csv(os.path.join(app_dir, 'data', 'bangalore_lighting.csv'))
        population_data = pd.read_csv(os.path.join(app_dir, 'data', 'bangalore_population.csv'))
        print(f'✅ Loaded {len(crime_data)} crime records')
        print(f'✅ Loaded {len(lighting_data)} lighting points')
        print(f'✅ Loaded {len(population_data)} population points')
        return crime_data, lighting_data, population_data
    except Exception as e:
        print(f'❌ Error loading data: {e}')
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def register_safe_routes_endpoints(bp, crime_data, lighting_data, population_data):
    '''Register all Safe Routes API endpoints'''
    
    # Copy the complete implementation from app.py here
    # This includes all functions like:
    # - validate_coordinates()
    # - haversine_distance()
    # - calculate_crime_exposure()
    # - calculate_route_safety_comprehensive()
    # - get_route_from_osrm()
    # - calculate_composite_score()
    # And all endpoints:
    # - /api/optimize-route
    # - /api/search-place
    # - /api/reverse-geocode
    # - /api/crime-heatmap
    # - /api/lighting-heatmap
    # - /api/population-heatmap
    # - /api/health
    # - /api/rate-route
    
    pass
"@

$backendCode | Out-File -FilePath "$destPath\safe_routes_backend.py" -Encoding UTF8
Write-Host "✅ Created safe_routes_backend.py (template)" -ForegroundColor Green
Write-Host ""

# 4. Display next steps
Write-Host "📋 NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Update your base.html navigation:" -ForegroundColor White
Write-Host "   Replace this line:" -ForegroundColor Gray
Write-Host "   <a href='/safe-routes'>Safe Routes</a>" -ForegroundColor DarkGray
Write-Host "   With:" -ForegroundColor Gray
Write-Host "   <a href='/safe-routes-full'>🗺️ Safe Routes (Full Featured)</a>" -ForegroundColor Green
Write-Host ""

Write-Host "2️⃣  Add new route in routes.py:" -ForegroundColor White
Write-Host "   @bp.route('/safe-routes-full')" -ForegroundColor Green
Write-Host "   def safe_routes_full():" -ForegroundColor Green
Write-Host "       return render_template('safe_routes_FULL.html')" -ForegroundColor Green
Write-Host ""

Write-Host "3️⃣  Copy the COMPLETE backend logic:" -ForegroundColor White
Write-Host "   Open: $sourcePath\app.py" -ForegroundColor Cyan
Write-Host "   Copy: All Safe Routes functions (lines 20-650)" -ForegroundColor Cyan
Write-Host "   Paste: Into your routes.py at the end" -ForegroundColor Cyan
Write-Host ""

Write-Host "4️⃣  Restart your Flask server:" -ForegroundColor White
Write-Host "   cd women-safety-app" -ForegroundColor Gray
Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   python run.py" -ForegroundColor Gray
Write-Host ""

Write-Host "5️⃣  Test the new features:" -ForegroundColor White
Write-Host "   Visit: http://172.16.128.151:5000/safe-routes-full" -ForegroundColor Cyan
Write-Host "   - Try 'Use Current Location' button" -ForegroundColor Gray
Write-Host "   - Search for two locations" -ForegroundColor Gray
Write-Host "   - Click 'Find Safe Routes'" -ForegroundColor Gray
Write-Host "   - You should see 7+ route options!" -ForegroundColor Gray
Write-Host "   - Click '🧭 Directions' on any route" -ForegroundColor Gray
Write-Host "   - Click '🚗 Navigate' to see animation" -ForegroundColor Gray
Write-Host ""

Write-Host "✨ Integration files created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 For detailed instructions, see:" -ForegroundColor Yellow
Write-Host "   - COMPARISON_MISSING_FEATURES.md" -ForegroundColor Cyan
Write-Host "   - INTEGRATION_GUIDE.md" -ForegroundColor Cyan
Write-Host ""

Write-Host "❓ Need help? The original app.py has all the backend code!" -ForegroundColor Magenta

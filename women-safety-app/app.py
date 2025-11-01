from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
import geocoder
from math import radians, cos, sin, asin, sqrt, atan2
import hashlib
from sqlalchemy import text

load_dotenv()

import os
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'app', 'templates')
static_dir = os.path.join(base_dir, 'app', 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
CORS(app)

# Add app configuration for database and sessions
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production-2024'
app.config['UPLOAD_FOLDER'] = 'app/uploads/evidence'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'women_safety.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
from app.models import db
from app.auth_models import User
db.init_app(app)

# Create tables and run migrations
with app.app_context():
    db.create_all()
    # Lightweight migration: add new columns if missing (SQLite only)
    try:
        with db.engine.connect() as conn:
            # Migrate users table
            res = conn.execute(text("PRAGMA table_info(users);"))
            existing_cols = {row[1] for row in res}
            user_cols = {
                'username': 'VARCHAR(50)',
                'home_city_district': 'TEXT',
                'address': 'TEXT',
                'age_range': 'TEXT',
                'gender_presentation': 'TEXT',
                'allergies': 'TEXT',
                'chronic_conditions': 'TEXT',
                'disability': 'TEXT',
                'primary_contact_name': 'TEXT',
                'primary_contact_phone': 'TEXT',
                'secondary_contact': 'TEXT',
                'consent_share_with_police': 'INTEGER',
                'consent_share_photo_with_police': 'INTEGER',
                'data_retention': 'TEXT'
            }
            for col, typ in user_cols.items():
                if col not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {typ};"))
                        conn.commit()
                    except Exception:
                        pass
            
            # Migrate incident_reports for additional_details
            res2 = conn.execute(text("PRAGMA table_info(incident_reports);"))
            existing_cols_ir = {row[1] for row in res2}
            if 'additional_details' not in existing_cols_ir:
                try:
                    conn.execute(text("ALTER TABLE incident_reports ADD COLUMN additional_details TEXT;"))
                    conn.commit()
                except Exception:
                    pass
            
            # Migrate community_posts for username system
            res3 = conn.execute(text("PRAGMA table_info(community_posts);"))
            existing_cols_cp = {row[1] for row in res3}
            community_cols = {
                'user_id': 'INTEGER',
                'username': 'VARCHAR(50)',
                'is_anonymous': 'INTEGER DEFAULT 1'
            }
            for col, typ in community_cols.items():
                if col not in existing_cols_cp:
                    try:
                        conn.execute(text(f"ALTER TABLE community_posts ADD COLUMN {col} {typ};"))
                        conn.commit()
                    except Exception:
                        pass
            
            # Migrate comments for username system
            res4 = conn.execute(text("PRAGMA table_info(comments);"))
            existing_cols_c = {row[1]: row[2] for row in res4}
            
            comment_cols = {
                'username': 'VARCHAR(50)',
                'is_anonymous': 'INTEGER DEFAULT 1'
            }
            for col, typ in comment_cols.items():
                if col not in existing_cols_c:
                    try:
                        conn.execute(text(f"ALTER TABLE comments ADD COLUMN {col} {typ};"))
                        conn.commit()
                    except Exception:
                        pass
            
            # Add user_id if it doesn't exist at all
            if 'user_id' not in existing_cols_c:
                try:
                    conn.execute(text("ALTER TABLE comments ADD COLUMN user_id INTEGER;"))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        print(f"Migration warning: {e}")
        pass

# Register blueprints
from app import routes
app.register_blueprint(routes.bp)

# Context processor to add today's date
@app.context_processor
def inject_today():
    return {'today': datetime.now().strftime('%Y-%m-%d')}

print("\n=== Initializing Safe Routes Backend ===")

try:
    print("Loading safety data...")
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    crime_data = pd.read_csv(os.path.join(base_dir, 'app', 'data', 'bangalore_crimes.csv'))
    lighting_data = pd.read_csv(os.path.join(base_dir, 'app', 'data', 'bangalore_lighting.csv'))
    population_data = pd.read_csv(os.path.join(base_dir, 'app', 'data', 'bangalore_population.csv'))
    print(f"✅ Loaded {len(crime_data)} crime records")
    print(f"✅ Loaded {len(lighting_data)} lighting points")
    print(f"✅ Loaded {len(population_data)} population points")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    raise

def validate_coordinates(lat, lon):
    BANGALORE_BOUNDS = {
        'min_lat': 12.704192, 'max_lat': 13.173706,
        'min_lon': 77.269876, 'max_lon': 77.850066
    }
    try:
        lat, lon = float(lat), float(lon)
        return (BANGALORE_BOUNDS['min_lat'] <= lat <= BANGALORE_BOUNDS['max_lat'] and
                BANGALORE_BOUNDS['min_lon'] <= lon <= BANGALORE_BOUNDS['max_lon'])
    except:
        return False

def haversine_distance(lat1, lon1, lat2, lon2):
    try:
        lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return c * 6371
    except Exception as e:
        print(f"❌ Error calculating distance: {e}")
        return float('inf')

def calculate_route_hash(route):
    if not route or len(route) < 2:
        return None
    sample_indices = [0, len(route)//4, len(route)//2, 3*len(route)//4, len(route)-1]
    sample_points = [route[i] for i in sample_indices if i < len(route)]
    hash_string = ''.join([f"{lat:.4f},{lon:.4f}" for lat, lon in sample_points])
    return hashlib.md5(hash_string.encode()).hexdigest()

def calculate_crime_exposure(lat, lon, radius=0.003):
    try:
        nearby_crimes = crime_data[
            (abs(crime_data['Latitude'] - lat) < radius) &
            (abs(crime_data['Longitude'] - lon) < radius)
        ]
        return len(nearby_crimes)
    except Exception as e:
        print(f"❌ Error calculating crime: {e}")
        return 0

def calculate_lighting_score(lat, lon, radius=0.005):
    try:
        nearby_lighting = lighting_data[
            (abs(lighting_data['Latitude'] - lat) < radius) &
            (abs(lighting_data['Longitude'] - lon) < radius)
        ]
        return nearby_lighting['lighting_score'].mean() if len(nearby_lighting) > 0 else 5.0
    except:
        return 5.0

def calculate_population_score(lat, lon, radius=0.005):
    try:
        nearby_pop = population_data[
            (abs(population_data['Latitude'] - lat) < radius) &
            (abs(population_data['Longitude'] - lon) < radius)
        ]
        if len(nearby_pop) > 0:
            return (
                nearby_pop['population_density'].mean() / 1000,
                nearby_pop['traffic_level'].mean() / 10,
                nearby_pop['is_main_road'].mean() > 0.5
            )
        return 5.0, 5.0, False
    except:
        return 5.0, 5.0, False

def calculate_route_safety_comprehensive(route, preferences=None):
    if not route or len(route) < 2:
        return None
    
    if preferences is None:
        preferences = {}
    
    try:
        sample_rate = max(1, len(route) // 50)
        sampled_route = route[::sample_rate]
        
        total_crime = 0
        max_crime_at_point = 0
        crime_hotspot_count = 0
        total_lighting = 0
        total_population = 0
        total_traffic = 0
        main_road_count = 0
        
        for lat, lon in sampled_route:
            crime_count = calculate_crime_exposure(lat, lon, radius=0.003)
            total_crime += crime_count
            max_crime_at_point = max(max_crime_at_point, crime_count)
            if crime_count > 3:
                crime_hotspot_count += 1
            
            light_score = calculate_lighting_score(lat, lon, radius=0.005)
            total_lighting += light_score
            
            pop_score, traffic_score, is_main_road = calculate_population_score(lat, lon, radius=0.005)
            total_population += pop_score
            total_traffic += traffic_score
            if is_main_road:
                main_road_count += 1
        
        n_points = len(sampled_route)
        
        avg_crime = total_crime / n_points
        avg_lighting = total_lighting / n_points
        avg_population = total_population / n_points
        avg_traffic = total_traffic / n_points
        main_road_pct = (main_road_count / n_points) * 100
        crime_hotspot_pct = (crime_hotspot_count / n_points) * 100
        
        base_crime_penalty = min(40, avg_crime ** 1.2 * 5)
        max_crime_penalty = min(40, max_crime_at_point ** 1.4 * 7)
        hotspot_penalty = min(30, crime_hotspot_pct * 0.5)
        
        total_crime_penalty = base_crime_penalty + max_crime_penalty + hotspot_penalty
        
        base_safety_score = max(0, 100 - total_crime_penalty)
        
        lighting_multiplier = 1.0 + (avg_lighting / 10) * (2.5 if preferences.get('prefer_well_lit') else 0.8)
        population_multiplier = 1.0 + (avg_population / 10) * (2.0 if preferences.get('prefer_populated') else 0.6)
        traffic_multiplier = 1.0 + (avg_traffic / 10) * (1.5 if preferences.get('prefer_populated') else 0.4)
        main_road_multiplier = 1.0 + (main_road_pct / 100) * (2.5 if preferences.get('prefer_main_roads') else 0.7)
        
        total_multiplier = (lighting_multiplier + population_multiplier + traffic_multiplier + main_road_multiplier) / 4
        
        final_safety_score = min(100, base_safety_score * total_multiplier)
        
        crime_density_score = 100 - min(100, avg_crime * 10)
        
        return {
            'safety_score': round(final_safety_score, 2),
            'crime_density': round(avg_crime, 2),
            'max_crime_exposure': round(max_crime_at_point, 2),
            'crime_hotspot_percentage': round(crime_hotspot_pct, 2),
            'lighting_score': round(avg_lighting, 2),
            'population_score': round(avg_population, 2),
            'traffic_score': round(avg_traffic, 2),
            'main_road_percentage': round(main_road_pct, 2),
            'crime_density_score': round(crime_density_score, 2)
        }
        
    except Exception as e:
        print(f"❌ Error calculating safety: {e}")
        return None

def get_route_from_osrm(start_lat, start_lon, end_lat, end_lon, waypoint=None):
    try:
        if not all(validate_coordinates(x, y) for x, y in [(start_lat, start_lon), (end_lat, end_lon)]):
            return None
        
        if waypoint:
            url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{waypoint['lon']},{waypoint['lat']};{end_lon},{end_lat}"
        else:
            url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
        
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'alternatives': 'true',
            'steps': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data['code'] != 'Ok':
            return None
        
        routes = []
        for route_data in data.get('routes', []):
            if 'geometry' not in route_data:
                continue
            
            coordinates = route_data['geometry']['coordinates']
            if not coordinates or len(coordinates) < 2:
                continue
            
            route = [[coord[1], coord[0]] for coord in coordinates]
            
            start_dist = haversine_distance(start_lat, start_lon, route[0][0], route[0][1])
            end_dist = haversine_distance(end_lat, end_lon, route[-1][0], route[-1][1])
            
            if start_dist > 0.2 or end_dist > 0.2:
                continue
            
            # Extract turn-by-turn instructions from OSRM
            steps = []
            if 'legs' in route_data:
                step_number = 1
                for leg in route_data['legs']:
                    if 'steps' in leg:
                        for step in leg['steps']:
                            if 'maneuver' in step:
                                instruction = step['maneuver'].get('instruction', step.get('name', 'Continue'))
                                distance = step.get('distance', 0)
                                steps.append({
                                    'number': step_number,
                                    'instruction': instruction,
                                    'distance': round(distance, 1),
                                    'distance_text': f"{distance:.0f}m" if distance < 1000 else f"{distance/1000:.1f}km"
                                })
                                step_number += 1
            
            routes.append({
                'route': route,
                'distance_km': route_data['distance'] / 1000,
                'duration_min': route_data['duration'] / 60,
                'waypoint': waypoint,
                'steps': steps
            })
        
        return routes
        
    except Exception as e:
        print(f"❌ OSRM error: {e}")
        return None

def calculate_composite_score(route, preferences):
    safety_weight = preferences.get('safety_weight', 0.7)
    distance_weight = preferences.get('distance_weight', 0.3)
    
    safety_score = route.get('safety_score', 50)
    distance_km = route.get('distance_km', 10)
    crime_density = route.get('crime_density', 5)
    max_crime = route.get('max_crime_exposure', 5)
    
    normalized_safety = safety_score / 100
    normalized_distance = max(0, 1 - (distance_km / 30))
    
    crime_penalty = (crime_density * 0.3 + max_crime * 0.7) / 20
    crime_penalty = min(1, crime_penalty)
    
    safety_component = normalized_safety * (1 - crime_penalty * 0.5)
    
    preference_bonus = 0
    if preferences.get('prefer_main_roads'):
        main_road_pct = route.get('main_road_percentage', 0)
        preference_bonus += (main_road_pct / 100) * 0.15
    
    if preferences.get('prefer_well_lit'):
        lighting_score = route.get('lighting_score', 5)
        preference_bonus += (lighting_score / 10) * 0.15
    
    if preferences.get('prefer_populated'):
        population_score = route.get('population_score', 5)
        preference_bonus += (population_score / 10) * 0.15
    
    composite_score = (safety_component * safety_weight + 
                      normalized_distance * distance_weight + 
                      preference_bonus)
    
    return composite_score

@app.route('/api/optimize-route', methods=['POST'])
def optimize_route():
    print("\n" + "="*60)
    print("=== OPTIMIZED ROUTE CALCULATION ===")
    print("="*60)
    
    try:
        data = request.json or {}
        if not all(k in data for k in ('start_lat', 'start_lon', 'end_lat', 'end_lon')):
            return jsonify({'success': False, 'error': 'Missing coordinates'}), 400

        try:
            start_lat = float(data.get('start_lat'))
            start_lon = float(data.get('start_lon'))
            end_lat = float(data.get('end_lat'))
            end_lon = float(data.get('end_lon'))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400

        preferences = {
            'prefer_main_roads': bool(data.get('prefer_main_roads', False)),
            'prefer_well_lit': bool(data.get('prefer_well_lit', False)),
            'prefer_populated': bool(data.get('prefer_populated', False)),
            'safety_weight': float(data.get('safety_weight', 0.7)),
            'distance_weight': float(data.get('distance_weight', 0.3))
        }
        
        print(f"\nRequest:")
        print(f"  Start: ({start_lat:.5f}, {start_lon:.5f})")
        print(f"  End: ({end_lat:.5f}, {end_lon:.5f})")
        print(f"  Safety weight: {preferences['safety_weight']:.2f}")
        print(f"  Distance weight: {preferences['distance_weight']:.2f}")
        print(f"  Main roads: {preferences['prefer_main_roads']}")
        print(f"  Well lit: {preferences['prefer_well_lit']}")
        print(f"  Populated: {preferences['prefer_populated']}")
        
        if not all(validate_coordinates(x, y) for x, y in [(start_lat, start_lon), (end_lat, end_lon)]):
            return jsonify({'success': False, 'error': 'Coordinates outside Bangalore'}), 400
        
        all_routes = []
        route_hashes = set()
        
        print("\n--- Phase 1: Direct Routes ---")
        direct_routes = get_route_from_osrm(start_lat, start_lon, end_lat, end_lon, waypoint=None)
        
        if direct_routes:
            print(f"OSRM returned {len(direct_routes)} direct alternatives")
            for idx, route_data in enumerate(direct_routes):
                route_hash = calculate_route_hash(route_data['route'])
                if route_hash and route_hash not in route_hashes:
                    safety = calculate_route_safety_comprehensive(route_data['route'], preferences)
                    if safety:
                        route_data.update(safety)
                        route_data['source'] = f'direct_{idx+1}'
                        route_data['type'] = 'direct'
                        all_routes.append(route_data)
                        route_hashes.add(route_hash)
                        print(f"✅ Direct route {idx+1}: {route_data['distance_km']:.2f}km, safety={safety['safety_score']:.1f}, crime={safety['crime_density']:.1f}")
        
        print("\n--- Phase 2: Strategic Waypoint Exploration ---")
        
        base_distance = haversine_distance(start_lat, start_lon, end_lat, end_lon)
        
        lat_diff = end_lat - start_lat
        lon_diff = end_lon - start_lon
        
        perp_lat = -lon_diff
        perp_lon = lat_diff
        perp_magnitude = sqrt(perp_lat**2 + perp_lon**2)
        
        if perp_magnitude > 0:
            perp_lat /= perp_magnitude
            perp_lon /= perp_magnitude
        
        positions = [0.25, 0.5, 0.75]
        offset_distances_km = [0.5, 1.2, 2.5]
        offsets = [d / 111.0 for d in offset_distances_km]
        directions = [1, -1]
        
        waypoint_count = 0
        max_waypoints = 25
        
        for position in positions:
            if waypoint_count >= max_waypoints:
                break
                
            for offset in offsets:
                if waypoint_count >= max_waypoints:
                    break
                    
                for direction in directions:
                    if waypoint_count >= max_waypoints:
                        break
                    
                    mid_lat = start_lat + lat_diff * position
                    mid_lon = start_lon + lon_diff * position
                    
                    wp_lat = mid_lat + perp_lat * offset * direction
                    wp_lon = mid_lon + perp_lon * offset * direction
                    
                    if not validate_coordinates(wp_lat, wp_lon):
                        continue
                    
                    wp_dist = (haversine_distance(start_lat, start_lon, wp_lat, wp_lon) + 
                              haversine_distance(wp_lat, wp_lon, end_lat, end_lon))
                    detour_ratio = wp_dist / base_distance if base_distance > 0 else 999
                    
                    if detour_ratio > 1.8:
                        continue
                    
                    waypoint_routes = get_route_from_osrm(start_lat, start_lon, end_lat, end_lon, 
                                                          waypoint={'lat': wp_lat, 'lon': wp_lon})
                    
                    if waypoint_routes:
                        for route_data in waypoint_routes:
                            route_hash = calculate_route_hash(route_data['route'])
                            
                            if route_hash and route_hash not in route_hashes:
                                safety = calculate_route_safety_comprehensive(route_data['route'], preferences)
                                if safety:
                                    route_data.update(safety)
                                    route_data['source'] = f'waypoint_{waypoint_count}'
                                    route_data['type'] = 'waypoint'
                                    
                                    all_routes.append(route_data)
                                    route_hashes.add(route_hash)
                                    waypoint_count += 1
                                    
                                    if waypoint_count >= max_waypoints:
                                        break
        
        print(f"Waypoint routes added: {waypoint_count}")
        print(f"\nTotal routes collected: {len(all_routes)}")
        
        if len(all_routes) == 0:
            return jsonify({'success': False, 'error': 'No valid routes found'}), 404
        
        print("\n--- Phase 3: Preference-Based Scoring ---")
        
        for route in all_routes:
            route['composite_score'] = calculate_composite_score(route, preferences)
        
        all_routes.sort(key=lambda x: x['composite_score'], reverse=True)
        
        final_routes = all_routes[:7]
        print(f"Final routes to display: {len(final_routes)}")
        
        for idx, route in enumerate(final_routes):
            route['rank'] = idx + 1
            route['is_recommended'] = (idx == 0)
            
            if idx == 0:
                category = 'best'
                emoji = '⭐'
                description = 'Best match for your preferences'
            elif route['crime_density'] <= 1.5 and route['max_crime_exposure'] <= 3:
                category = 'safest'
                emoji = '🛡️'
                description = 'Safest route (avoids crime hotspots)'
            elif route['distance_km'] <= min(r['distance_km'] for r in final_routes) * 1.05:
                category = 'fastest'
                emoji = '⚡'
                description = 'Shortest distance'
            elif route['main_road_percentage'] >= 70:
                category = 'main_roads'
                emoji = '🛣️'
                description = 'Uses main roads'
            else:
                category = 'balanced'
                emoji = '⚖️'
                description = 'Well-balanced option'
            
            route['category'] = category
            route['emoji'] = emoji
            route['description'] = description
            
            route['distance_display'] = f"{route['distance_km']:.2f} km"
            route['duration_display'] = f"{int(route['duration_min'])} min"
            route['safety_display'] = f"{route['safety_score']:.0f}/100"
            
            reasons = []
            
            if route.get('crime_density', 5) <= 1:
                reasons.append("Very low crime area")
            elif route.get('crime_density', 5) <= 2:
                reasons.append("Low crime density")
            elif route.get('crime_density', 5) > 4:
                reasons.append(f"⚠️ Crime density: {route['crime_density']:.1f}")
            
            if route.get('max_crime_exposure', 0) <= 2:
                reasons.append("No crime hotspots")
            elif route.get('max_crime_exposure', 0) <= 5:
                reasons.append("Minimal crime exposure")
            else:
                reasons.append(f"⚠️ Max crime exposure: {route['max_crime_exposure']:.0f}")
            
            if route.get('main_road_percentage', 0) > 70:
                reasons.append(f"{route['main_road_percentage']:.0f}% main roads")
            if route.get('lighting_score', 0) > 7.5:
                reasons.append("Well-lit area")
            if route.get('population_score', 0) > 6:
                reasons.append("Populated area")
            
            route['reasons'] = reasons
            
            if route.get('max_crime_exposure', 0) > 8 or route.get('crime_density', 0) > 5:
                route['warning'] = "⚠️ High crime exposure"
            elif route.get('max_crime_exposure', 0) > 5 or route.get('crime_density', 0) > 3:
                route['warning'] = "⚠️ Moderate crime exposure"
            else:
                route['warning'] = None
            
            route.pop('waypoint', None)
            route.pop('composite_score', None)
        
        print("\n" + "="*60)
        print(f"✅ Optimization complete: {len(final_routes)} routes")
        print(f"Top route: Safety={final_routes[0]['safety_score']:.1f}, Distance={final_routes[0]['distance_km']:.2f}km, Crime={final_routes[0]['crime_density']:.1f}")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'routes': final_routes,
            'total_analyzed': len(all_routes),
            'message': f'Found {len(final_routes)} optimized routes'
        })
        
    except Exception as e:
        print(f"\n❌ Error in route optimization: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search-place', methods=['GET'])
def search_place():
    q = request.args.get('q')
    if not q:
        return jsonify({'success': False, 'error': 'No query provided'}), 400

    try:
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': q + ', Bangalore, India',
            'format': 'jsonv2',
            'addressdetails': 1,
            'limit': 6,
            'accept-language': 'en'
        }
        headers = {'User-Agent': 'safe-routes-app/1.0'}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        data = resp.json()

        results = []
        for item in data:
            try:
                lat = float(item.get('lat', 0))
                lon = float(item.get('lon', 0))
                if validate_coordinates(lat, lon):
                    results.append({
                        'display_name': item.get('display_name'),
                        'lat': lat,
                        'lon': lon,
                        'type': item.get('type')
                    })
            except:
                continue

        return jsonify({'success': True, 'results': results})
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reverse-geocode', methods=['GET'])
def reverse_geocode():
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon or not validate_coordinates(lat, lon):
            return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400

        url = 'https://nominatim.openstreetmap.org/reverse'
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'jsonv2',
            'accept-language': 'en'
        }
        headers = {'User-Agent': 'safe-routes-app/1.0'}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        data = resp.json()
        
        return jsonify({
            'success': True,
            'address': data.get('display_name')
        })
    except Exception as e:
        print(f"❌ Reverse geocoding error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/crime-heatmap', methods=['GET'])
def get_crime_heatmap():
    heatmap_data = crime_data[['Latitude', 'Longitude']].values.tolist()
    return jsonify({
        'success': True,
        'data': heatmap_data,
        'total_crimes': len(crime_data)
    })

@app.route('/api/lighting-heatmap', methods=['GET'])
def get_lighting_heatmap():
    try:
        if 'lighting_score' in lighting_data.columns:
            points = lighting_data[['Latitude', 'Longitude', 'lighting_score']].values.tolist()
        else:
            points = lighting_data[['Latitude', 'Longitude']].assign(lighting_score=5.0).values.tolist()
        return jsonify({
            'success': True,
            'data': points,
            'total_locations': len(points)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/population-heatmap', methods=['GET'])
def get_population_heatmap():
    try:
        if 'population_density' in population_data.columns:
            points = population_data[['Latitude', 'Longitude', 'population_density']].values.tolist()
        else:
            points = population_data[['Latitude', 'Longitude']].assign(population_density=1.0).values.tolist()
        return jsonify({
            'success': True,
            'data': points,
            'total_locations': len(points)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'message': 'Backend is running',
        'crimes_loaded': len(crime_data),
        'lighting_points': len(lighting_data),
        'population_points': len(population_data)
    })

@app.route('/api/rate-route', methods=['POST'])
def rate_route():
    try:
        data = request.json or {}
        return jsonify({'success': True, 'message': 'Rating recorded'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Note: Main routes (/, /login, /signup, /safe-routes, etc.) are handled by the blueprint

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Women's Safety App - FULL APPLICATION")
    print("="*60)
    print(f"📊 Crime data: {len(crime_data)} records")
    print(f"💡 Lighting data: {len(lighting_data)} points")
    print(f"👥 Population data: {len(population_data)} points")
    print("\nFeatures Available:")
    print("✅ User Authentication (Login/Signup)")
    print("✅ Incident Reporting")
    print("✅ Safe Routes with crime analysis")
    print("✅ Community Support")
    print("✅ SOS Center")
    print("✅ Emergency Contacts")
    print("✅ Fake Call Feature")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
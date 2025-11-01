from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response, abort
from werkzeug.utils import secure_filename
import os
import json
import requests
from datetime import datetime
from app.models import db, IncidentReport, CommunityPost, Comment, EmergencyContact, SOSAlert, UserPreference, RouteFeedback
from sqlalchemy import text
from app.auth_models import User
from flask import send_from_directory

bp = Blueprint('main', __name__)

# Gemini API configuration
GEMINI_API_KEY = 'AIzaSyCWa3C1wZ0cG1bSdEqFAdHs826i34HY5k0'
# Use Gemini 2.0 Flash - latest stable model
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'm4a', 'mp4', 'mov', 'pdf', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============ AUTHENTICATION ROUTES ============
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Set session
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name
            session['username'] = user.username
            session['default_anonymous'] = user.default_anonymous
            session['logged_in'] = True
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Welcome back! You are now logged in.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html')

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        default_anonymous = request.form.get('default_anonymous') == 'on'

        # Extended profile fields (all optional)
        home_city_district = request.form.get('home_city_district')
        address = request.form.get('address')
        age_range = request.form.get('age_range')
        gender_presentation = request.form.get('gender_presentation')
        allergies = request.form.get('allergies')
        chronic_conditions = request.form.get('chronic_conditions')
        disability = request.form.get('disability')
        primary_contact_name = request.form.get('primary_contact_name')
        primary_contact_phone = request.form.get('primary_contact_phone')
        secondary_contact = request.form.get('secondary_contact')
        consent_share_with_police = request.form.get('consent_share_with_police') == 'on'
        consent_share_photo_with_police = request.form.get('consent_share_photo_with_police') == 'on'
        data_retention = request.form.get('data_retention') or '1y'
        
        # Validation
        if not phone or not phone.strip():
            flash('Phone number is required.', 'danger')
            return render_template('signup.html')
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('signup.html')
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login instead.', 'warning')
            return redirect(url_for('main.login'))
        
        # Check if username already exists
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash('Username already taken. Please choose a different username.', 'warning')
            return render_template('signup.html')
        
        # Create new user
        new_user = User(
            username=username,
            name=name,
            email=email,
            phone=phone,
            default_anonymous=default_anonymous,
            home_city_district=home_city_district,
            address=address,
            age_range=age_range,
            gender_presentation=gender_presentation,
            allergies=allergies,
            chronic_conditions=chronic_conditions,
            disability=disability,
            primary_contact_name=primary_contact_name,
            primary_contact_phone=primary_contact_phone,
            secondary_contact=secondary_contact,
            consent_share_with_police=consent_share_with_police,
            consent_share_photo_with_police=consent_share_photo_with_police,
            data_retention=data_retention
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Auto login
        session['user_id'] = new_user.id
        session['user_email'] = new_user.email
        session['user_name'] = new_user.name
        session['username'] = new_user.username
        session['default_anonymous'] = new_user.default_anonymous
        session['logged_in'] = True
        
        flash('Account created successfully! Welcome to SafeSpace.', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('signup.html')

@bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    user = User.query.get(session.get('user_id'))
    if not user:
        abort(404)
    if request.method == 'POST':
        # Update username if changed
        new_username = request.form.get('username', '').strip()
        if new_username and new_username != user.username:
            # Check if username is already taken
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                flash('Username already taken. Please choose a different username.', 'warning')
                return render_template('settings.html', user=user)
            user.username = new_username
            session['username'] = new_username
        
        # Update privacy settings
        user.default_anonymous = request.form.get('default_anonymous') == 'on'
        user.consent_share_with_police = request.form.get('consent_share_with_police') == 'on'
        user.consent_share_photo_with_police = request.form.get('consent_share_photo_with_police') == 'on'
        user.data_retention = request.form.get('data_retention') or user.data_retention
        
        db.session.commit()
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('main.settings'))
    return render_template('settings.html', user=user)

@bp.route('/profile/export')
def export_profile():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    user = User.query.get(session.get('user_id'))
    if not user:
        abort(404)
    data = user.to_dict()
    # Do not include password hash
    data.pop('password_hash', None)
    # Include minimal report ids for context
    data['report_ids'] = [r.id for r in user.reports] if hasattr(user, 'reports') else []
    response = make_response(json.dumps(data, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=profile_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

# ---------------- SOS Center API Helpers -----------------
def _ensure_dirs():
    base_dir = os.path.join('app', 'uploads', 'sos')
    logs_dir = os.path.join(base_dir, 'logs')
    rec_dir = os.path.join(base_dir, 'recordings')
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(rec_dir, exist_ok=True)
    return base_dir, logs_dir, rec_dir

def _append_json(path, entry):
    data = []
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = []
    data.append(entry)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def send_sms_alert(contacts, user_name, location_link, battery_level, user_phone=None):
    """
    Send SMS alerts to emergency contacts using the user's own phone number as sender
    """
    try:
        bl = int(battery_level)
        battery_text = f"{bl}%"
    except Exception:
        battery_text = "Unknown"
    # Choose message style: 'otp' (concise, no emoji) or 'rich' (default)
    sms_style = os.environ.get('SMS_STYLE', 'rich').lower()
    if sms_style == 'otp':
        message = (
            f"ALERT: {user_name} needs help. "
            f"Live: {location_link} "
            f"Battery: {battery_text} "
            f"Time: {datetime.utcnow().strftime('%I:%M %p')}"
        )
    else:
        message = (
            f"🚨 EMERGENCY ALERT from {user_name}! Location: {location_link} | "
            f"Battery: {battery_text} | Time: {datetime.utcnow().strftime('%I:%M %p')}"
        )
    
    real_sent = 0
    provider = "MOCK"
    
    # Try Fast2SMS with user's own number as sender
    fast2sms_key = os.environ.get('FAST2SMS_API_KEY')
    if fast2sms_key and user_phone:
        try:
            import requests
            provider = "Fast2SMS"
            
            # Format user's phone for sender_id
            sender_phone = user_phone.strip().replace('+', '').replace('-', '').replace(' ', '')
            if sender_phone.startswith('91') and len(sender_phone) == 12:
                sender_phone = sender_phone[2:]  # Remove country code for 10-digit
            
            for c in contacts:
                try:
                    # Format recipient number
                    phone = c.phone.strip().replace('+', '').replace('-', '').replace(' ', '')
                    if phone.startswith('91') and len(phone) == 12:
                        phone = phone[2:]
                    
                    url = "https://www.fast2sms.com/dev/bulkV2"
                    # Add sender info to message instead of sender_id (not supported by Fast2SMS free plan)
                    alert_msg = f"[From {sender_phone}] {message}"
                    payload = {
                        "route": "q",
                        "message": alert_msg,
                        "language": "english",
                        "flash": 0,
                        "numbers": phone
                    }
                    headers = {
                        "authorization": fast2sms_key,
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                    resp = requests.post(url, data=payload, headers=headers, timeout=10)
                    if resp.status_code == 200 and resp.json().get('return'):
                        real_sent += 1
                    else:
                        print(f"[Fast2SMS] Failed to send to {c.phone}: {resp.text}")
                except Exception as sms_err:
                    print(f"[Fast2SMS] Failed to send to {c.phone}: {sms_err}")
        except Exception as e:
            print(f"[Fast2SMS] Error: {e}")
            provider = "MOCK"
    
    # Fallback to Twilio with user's number (if verified)
    if provider == "MOCK":
        tw_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        tw_token = os.environ.get('TWILIO_AUTH_TOKEN')
        if tw_sid and tw_token and user_phone:
            try:
                from twilio.rest import Client  # type: ignore
                client = Client(tw_sid, tw_token)
                provider = "Twilio"
                
                # Format user's phone for Twilio (E.164)
                from_number = user_phone.strip()
                if not from_number.startswith('+'):
                    from_number = '+' + from_number
                
                for c in contacts:
                    try:
                        to_number = c.phone.strip()
                        if not to_number.startswith('+'):
                            to_number = '+' + to_number
                        client.messages.create(body=message, from_=from_number, to=to_number)
                        real_sent += 1
                    except Exception as sms_err:
                        print(f"[Twilio] Failed to send to {c.phone}: {sms_err}")
            except Exception as e:
                print(f"[Twilio] Error: {e}")
                provider = "MOCK"

    # Console log (always) for visibility
    print(f"\n{'='*60}")
    sender_info = f" (from {user_phone})" if user_phone else ""
    print(f"{provider} SMS ALERT{sender_info} | SENT: {real_sent}/{len(contacts)}")
    if real_sent == 0 and provider != "MOCK":
        print(f"⚠️  API SMS failed - User will send via phone's SMS app (no payment needed)")
    print(f"{'='*60}")
    for contact in contacts:
        print(f"To: {contact.name} ({contact.phone})")
        print(f"Message: {message}")
        print(f"-"*60)
    
    # Log to JSON file
    _, logs_dir, _ = _ensure_dirs()
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'message': message,
        'contacts': [{'name': c.name, 'phone': c.phone, 'relationship': c.relationship} for c in contacts],
        'type': 'SOS_ALERT'
    }
    _append_json(os.path.join(logs_dir, 'sms_log.json'), log_entry)
    
    return real_sent if real_sent > 0 else len(contacts)

def send_all_clear_sms(contacts, user_name, user_phone=None):
    """Send 'All Clear' message using user's own phone number"""
    sms_style = os.environ.get('SMS_STYLE', 'rich').lower()
    if sms_style == 'otp':
        message = f"SAFE: {user_name} alert cancelled at {datetime.utcnow().strftime('%I:%M %p')}"
    else:
        message = f"✅ {user_name} has marked themselves as safe. Emergency alert cancelled at {datetime.utcnow().strftime('%I:%M %p')}."
    
    real_sent = 0
    provider = "MOCK"
    
    # Try Fast2SMS with user's number
    fast2sms_key = os.environ.get('FAST2SMS_API_KEY')
    if fast2sms_key and user_phone:
        try:
            import requests
            provider = "Fast2SMS"
            
            sender_phone = user_phone.strip().replace('+', '').replace('-', '').replace(' ', '')
            if sender_phone.startswith('91') and len(sender_phone) == 12:
                sender_phone = sender_phone[2:]
            
            for c in contacts:
                try:
                    phone = c.phone.strip().replace('+', '').replace('-', '').replace(' ', '')
                    if phone.startswith('91') and len(phone) == 12:
                        phone = phone[2:]
                    
                    url = "https://www.fast2sms.com/dev/bulkV2"
                    # Add sender info to message
                    clear_msg = f"[From {sender_phone}] {message}"
                    payload = {
                        "route": "q",
                        "message": clear_msg,
                        "language": "english",
                        "flash": 0,
                        "numbers": phone
                    }
                    headers = {
                        "authorization": fast2sms_key,
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                    resp = requests.post(url, data=payload, headers=headers, timeout=10)
                    if resp.status_code == 200 and resp.json().get('return'):
                        real_sent += 1
                except Exception as sms_err:
                    print(f"[Fast2SMS] Failed to send ALL CLEAR to {c.phone}: {sms_err}")
        except Exception as e:
            print(f"[Fast2SMS] Error: {e}")
            provider = "MOCK"
    
    # Fallback to Twilio with user's number
    if provider == "MOCK":
        tw_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        tw_token = os.environ.get('TWILIO_AUTH_TOKEN')
        if tw_sid and tw_token and user_phone:
            try:
                from twilio.rest import Client  # type: ignore
                client = Client(tw_sid, tw_token)
                provider = "Twilio"
                
                from_number = user_phone.strip()
                if not from_number.startswith('+'):
                    from_number = '+' + from_number
                
                for c in contacts:
                    try:
                        to_number = c.phone.strip()
                        if not to_number.startswith('+'):
                            to_number = '+' + to_number
                        client.messages.create(body=message, from_=from_number, to=to_number)
                        real_sent += 1
                    except Exception as sms_err:
                        print(f"[Twilio] Failed to send ALL CLEAR to {c.phone}: {sms_err}")
            except Exception as e:
                print(f"[Twilio] Error: {e}")
                provider = "MOCK"

    # Console log
    print(f"\n{'='*60}")
    sender_info = f" (from {user_phone})" if user_phone else ""
    print(f"{provider} ALL CLEAR SMS{sender_info} | SENT: {real_sent}/{len(contacts)}")
    print(f"{'='*60}")
    for contact in contacts:
        print(f"To: {contact.name} ({contact.phone})")
        print(f"Message: {message}")
        print(f"-"*60)
    
    _, logs_dir, _ = _ensure_dirs()
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'message': message,
        'contacts': [{'name': c.name, 'phone': c.phone, 'relationship': c.relationship} for c in contacts],
        'type': 'ALL_CLEAR'
    }
    _append_json(os.path.join(logs_dir, 'sms_log.json'), log_entry)
    
    return real_sent if real_sent > 0 else len(contacts)

@bp.route('/profile/delete', methods=['POST'])
def delete_profile():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))
    user = User.query.get(session.get('user_id'))
    if not user:
        abort(404)
    # Delete related data: comments made anonymously are not linked to user; delete user's reports & posts
    reports = IncidentReport.query.filter_by(user_id=user.id).all()
    for report in reports:
        # Delete community post if exists
        post = CommunityPost.query.filter_by(report_id=report.id).first()
        if post:
            Comment.query.filter_by(post_id=post.id).delete()
            db.session.delete(post)
        db.session.delete(report)
    # Delete profile photo file if exists
    try:
        if user.photo_path:
            photo_abs = os.path.join('app', user.photo_path.replace('uploads/', 'uploads/'))
            # Normalize path and remove file if present
            photo_abs = os.path.join('app', user.photo_path) if not user.photo_path.startswith('app') else user.photo_path
            if os.path.exists(photo_abs):
                os.remove(photo_abs)
    except Exception:
        pass
    # Finally delete user
    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash('Your account and associated data have been permanently deleted.', 'info')
    return redirect(url_for('main.signup'))

@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.login'))

@bp.route('/my_reports')
def my_reports():
    """Display user's incident reports"""
    if not session.get('logged_in'):
        flash('Please log in to view your reports.', 'warning')
        return redirect(url_for('main.login'))
    
    user_id = session.get('user_id')
    reports = IncidentReport.query.filter_by(user_id=user_id).order_by(IncidentReport.created_at.desc()).all()
    
    return render_template('my_reports.html', reports=reports)

@bp.route('/fake-call')
def fake_call():
    """AI-powered Fake Call (main). Use ?basic=1 to load legacy template as backup."""
    basic = request.args.get('basic', '').lower() in ('1', 'true', 'yes')
    if basic:
        return render_template('fake_call.html')
    return render_template('fake_call_ai.html')

@bp.route('/fake-call-basic')
def fake_call_basic():
    """Legacy/basic fake call kept as backup"""
    return render_template('fake_call.html')

@bp.route('/sos-center')
def sos_center():
    """Emergency SOS Center page"""
    # Use the original SOS Center layout (now with upgraded features)
    return render_template('sos_center.html')

@bp.route('/sos-pro')
def sos_pro():
    """Enhanced SOS page (ported from WOMENbest index.html)"""
    return render_template('sos_pro.html')

@bp.route('/api/sos-profile', methods=['GET'])
def api_sos_profile():
    """Return minimal profile data to prefill SOS page from signup info."""
    if not session.get('logged_in'):
        return jsonify({
            'success': False,
            'error': 'Not logged in',
            'profile': {
                'name': None,
                'bloodType': None,
                'medicalInfo': None,
                'emergencyNote': None
            }
        }), 401

    user = User.query.get(session.get('user_id'))
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Helpers to normalize blank-ish values like '-', 'NA', 'N/A', 'None'
    def _clean(val):
        if val is None:
            return None
        s = str(val).strip()
        if s.lower() in { '-', 'na', 'n/a', 'none' }:
            return None
        return s

    # Map fields from User model
    name = _clean(user.name) or user.username or 'User'
    blood = _clean(user.blood_group)
    # Merge allergies and chronic conditions into a compact medical info string
    med_parts = []
    a = _clean(user.allergies)
    c = _clean(user.chronic_conditions)
    if a:
        med_parts.append(f"Allergies: {a}")
    if c:
        med_parts.append(f"Conditions: {c}")
    medical = '; '.join(med_parts) if med_parts else None
    # Provide a gentle default note with preferred contact if present
    note = None
    if _clean(user.primary_contact_name) or _clean(user.primary_contact_phone):
        pc_name = _clean(user.primary_contact_name) or 'Primary contact'
        pc_phone = _clean(user.primary_contact_phone) or ''
        note = f"Preferred contact: {pc_name} {pc_phone}".strip()

    return jsonify({
        'success': True,
        'profile': {
            'name': name,
            'bloodType': blood,
            'medicalInfo': medical,
            'emergencyNote': note
        }
    })

@bp.route('/emergency-contacts')
def emergency_contacts():
    """Emergency contacts management page"""
    if 'user_id' not in session:
        flash('Please log in to manage your emergency contacts', 'warning')
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    contacts = EmergencyContact.query.filter_by(user_id=user_id, is_active=True).order_by(EmergencyContact.priority).all()
    return render_template('emergency_contacts.html', contacts=contacts)

@bp.route('/api/emergency-contacts', methods=['POST'])
def api_add_contact():
    """Add new emergency contact"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    
    # Validate input
    if not data.get('name') or not data.get('phone') or not data.get('relationship'):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Check if user already has 4 contacts (maximum)
    existing_count = EmergencyContact.query.filter_by(user_id=user_id, is_active=True).count()
    if existing_count >= 4:
        return jsonify({'success': False, 'error': 'Maximum 4 emergency contacts allowed'}), 400
    
    # Create new contact
    contact = EmergencyContact(
        user_id=user_id,
        name=data['name'],
        phone=data['phone'],
        relationship=data['relationship'],
        priority=data.get('priority', 1)
    )
    
    try:
        db.session.add(contact)
        db.session.commit()
        return jsonify({'success': True, 'contact': contact.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/emergency-contacts/<int:contact_id>', methods=['PUT'])
def api_update_contact(contact_id):
    """Update emergency contact"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    contact = EmergencyContact.query.filter_by(id=contact_id, user_id=user_id, is_active=True).first()
    
    if not contact:
        return jsonify({'success': False, 'error': 'Contact not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'name' in data:
        contact.name = data['name']
    if 'phone' in data:
        contact.phone = data['phone']
    if 'relationship' in data:
        contact.relationship = data['relationship']
    if 'priority' in data:
        contact.priority = data['priority']
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'contact': contact.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/emergency-contacts/<int:contact_id>', methods=['DELETE'])
def api_delete_contact(contact_id):
    """Delete emergency contact (soft delete)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    contact = EmergencyContact.query.filter_by(id=contact_id, user_id=user_id, is_active=True).first()
    
    if not contact:
        return jsonify({'success': False, 'error': 'Contact not found'}), 404
    
    # Soft delete
    contact.is_active = False
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/emergency-contacts', methods=['GET'])
def api_get_contacts():
    """Get user's emergency contacts"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in', 'contacts': []}), 401
    
    user_id = session['user_id']
    contacts = EmergencyContact.query.filter_by(user_id=user_id, is_active=True).order_by(EmergencyContact.priority).all()
    
    return jsonify({
        'success': True,
        'contacts': [contact.to_dict() for contact in contacts]
    })

@bp.route('/track/<int:sos_id>')
def track_sos(sos_id):
    """Public SOS tracking page"""
    alert = SOSAlert.query.get_or_404(sos_id)
    return render_template('sos_track.html', alert=alert, sos_id=sos_id)

@bp.route('/api/sos-track/<int:sos_id>')
def api_sos_track(sos_id):
    """Get SOS tracking data"""
    alert = SOSAlert.query.get_or_404(sos_id)
    
    # Get location history from JSON log
    _, logs_dir, _ = _ensure_dirs()
    locations = []
    try:
        log_path = os.path.join(logs_dir, 'live_locations_log.json')
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                all_locations = json.load(f)
                # Filter by sosId
                locations = [loc for loc in all_locations if loc.get('sosId') == sos_id]
    except Exception as e:
        print(f"Error reading locations: {e}")
    
    return jsonify({
        'success': True,
        'alert': alert.to_dict(),
        'locations': locations
    })

@bp.route('/sos-deactivate')
def sos_deactivate_page():
    """SOS deactivation page"""
    if 'user_id' not in session:
        flash('Please log in to deactivate alerts', 'warning')
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    # Get the most recent active alert for this user
    alert = SOSAlert.query.filter_by(user_id=user_id, is_active=True).order_by(SOSAlert.trigger_time.desc()).first()
    
    return render_template('sos_deactivate.html', alert=alert)

@bp.route('/api/sos-deactivate', methods=['POST'])
def api_sos_deactivate():
    """Deactivate SOS alert with PIN verification"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    alert_id = data.get('alert_id')
    pin = data.get('pin')
    
    if not alert_id or not pin:
        return jsonify({'success': False, 'error': 'Missing alert ID or PIN'}), 400
    
    # Get user and alert
    user = User.query.get(user_id)
    alert = SOSAlert.query.filter_by(id=alert_id, user_id=user_id, is_active=True).first()
    
    if not alert:
        return jsonify({'success': False, 'error': 'Alert not found or already deactivated'}), 404
    
    # Verify PIN (if user has set one, otherwise allow any 4+ digit PIN)
    if user.emergency_pin_hash:
        if not user.check_emergency_pin(pin):
            return jsonify({'success': False, 'error': 'Incorrect PIN'}), 401
    elif len(str(pin)) < 4:
        return jsonify({'success': False, 'error': 'PIN must be at least 4 digits'}), 400
    
    # Deactivate alert
    alert.is_active = False
    alert.resolved_at = datetime.utcnow()
    alert.resolution_pin_verified = True
    
    try:
        db.session.commit()
        
        # Send "All Clear" SMS to emergency contacts
        contacts = EmergencyContact.query.filter_by(user_id=user_id, is_active=True).all()
        if contacts:
            user_name = user.username if user else 'User'
            user_phone = user.phone if user else None
            send_all_clear_sms(contacts, user_name, user_phone)
        
        contact_count = len(contacts)
        
        return jsonify({
            'success': True,
            'message': f'Alert deactivated successfully. {contact_count} contacts have been notified.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/onboarding')
def onboarding():
    """Onboarding page with permission requests for first-time users"""
    return render_template('onboarding.html')

@bp.route('/')
def index():
    """Landing page with introduction to Gringotts"""
    return render_template('landing.html')

@bp.route('/report')
def report_incident():
    """Incident report form"""
    return render_template('incident_report_enhanced.html')

@bp.route('/submit_report', methods=['POST'])
def submit_report():
    # Collect form data
    report_data = {
        'who_involved': request.form.get('who_involved'),
        'who_sub_option': request.form.get('who_sub_option'),
        'incident_type': request.form.get('incident_type'),
        'incident_sub_type': request.form.get('incident_sub_type'),
        'location': request.form.get('location'),
        'location_detail': request.form.get('location_detail'),
        'impact': request.form.getlist('impact'),  # Multiple selections allowed
        'impact_details': request.form.getlist('impact_details'),
        'incident_date': request.form.get('incident_date'),
        'incident_time': request.form.get('incident_time'),
        'first_time': request.form.get('first_time'),
        'frequency': request.form.get('frequency'),
        'additional_details': request.form.get('additional_details', '')
    }
    
    # Handle file uploads
    uploaded_files = []
    if 'evidence_files' in request.files:
        files = request.files.getlist('evidence_files')
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                
                # Create directory if it doesn't exist
                upload_dir = os.path.join('app', 'uploads', 'evidence')
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, unique_filename)
                file.save(file_path)
                uploaded_files.append(unique_filename)
    
    report_data['evidence_files'] = uploaded_files

    # Determine display name preference BEFORE generating summary
    user_id = session.get('user_id')
    is_anonymous = True  # Default to anonymous
    display_name = 'Anonymous'
    if user_id:
        user = User.query.get(user_id)
        if user:
            is_anonymous = user.default_anonymous
            preferred = user.username or user.name
            if preferred and not is_anonymous:
                display_name = preferred
    report_data['display_name'] = display_name

    # Generate AI summary using Gemini (uses display_name and avoids placeholders)
    summary = generate_ai_summary(report_data)
    
    # Save to database
    incident_report = IncidentReport(
        user_id=user_id,
        is_anonymous=is_anonymous,
        who_involved=report_data['who_involved'],
        who_sub_option=report_data.get('who_sub_option'),
        incident_type=report_data['incident_type'],
        incident_sub_type=report_data.get('incident_sub_type'),
        location=report_data['location'],
        location_detail=report_data.get('location_detail'),
        impact=request.form.get('impact'),  # Single selection now
        impact_detail_severity=request.form.get('impact_detail_severity'),
        impact_detail_symptoms=request.form.get('impact_detail_symptoms'),
        impact_detail_harm_type=request.form.get('impact_detail_harm_type'),
        impact_detail_medical=request.form.get('impact_detail_medical'),
        impact_detail_financial=request.form.get('impact_detail_financial'),
        impact_detail_loss_type=request.form.get('impact_detail_loss_type'),
        impact_detail_reputation=request.form.get('impact_detail_reputation'),
        impact_detail_ongoing=request.form.get('impact_detail_ongoing'),
        impact_detail_fear_level=request.form.get('impact_detail_fear_level'),
        impact_detail_fear_type=request.form.get('impact_detail_fear_type'),
        impact_detail_sleep=request.form.get('impact_detail_sleep'),
        impact_detail_sleep_type=request.form.get('impact_detail_sleep_type'),
        impact_detail_other=request.form.get('impact_detail_other'),
        incident_date=datetime.strptime(report_data['incident_date'], '%Y-%m-%d').date() if report_data.get('incident_date') else None,
        incident_time=report_data.get('incident_time'),
        first_time=report_data.get('first_time'),
        frequency=report_data.get('frequency'),
        additional_details=report_data.get('additional_details'),
        ai_summary=summary
    )
    
    db.session.add(incident_report)
    db.session.commit()
    
    # Store in session for next page
    session['report_data'] = report_data
    session['ai_summary'] = summary
    session['report_id'] = incident_report.id
    
    return redirect(url_for('main.show_summary'))

def generate_ai_summary(data):
    """Generate incident report summary using Gemini AI"""
    # Build prompt with strict guidance to never use placeholders like [Your Name]
    # and to default to "Anonymous" when name is not provided or anonymity is chosen.
    incident = data.get('incident_type') or 'Not specified'
    who = data.get('who_involved') or 'Not specified'
    location = data.get('location') or 'Not specified'
    impact_list = data.get('impact') or []
    impact = ', '.join(impact_list) if isinstance(impact_list, list) else (impact_list or 'Not specified')
    person = data.get('display_name') or 'Anonymous'
    date_str = data.get('incident_date') or 'Not specified'

    prompt = (
        "Write a concise, professional incident summary in a single paragraph of EXACTLY 100 to 120 words. "
        "Do not use section headers, bullets, or any placeholder text like [Your Name] or [Security/Supervisor]. "
        "If a person’s name is unavailable or anonymity is chosen, refer to them as 'Anonymous'. "
        "Incorporate these details naturally: incident type, who was involved, location, approximate date/time if provided, and key impacts. "
        "Use neutral tone, avoid sensitive identifiers, and prefer general phrasing over specifics that could deanonymize. "
        f"Details to include: Person: {person}; Incident: {incident}; Who involved: {who}; Location: {location}; Date: {date_str}; Impact: {impact}."
    )

    # Call Gemini API and return the generated summary with sensible fallbacks
    try:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 300}
        }
        response = requests.post(
            GEMINI_API_URL,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text'].strip()
            # No content returned
            return (
                f"Anonymous reported an incident involving {who} at {location}. "
                f"Impacts noted: {impact}. Date: {date_str}."
            )
        # API error fallback
        return (
            f"Anonymous reported an incident involving {who} at {location}. "
            f"Impacts noted: {impact}. Date: {date_str}."
        )
    except Exception:
        # Network or parsing error fallback
        return (
            f"Anonymous reported an incident involving {who} at {location}. "
            f"Impacts noted: {impact}. Date: {date_str}."
        )

def generate_first_person_story(data, ai_summary):
    """Rewrite the AI summary into an empathetic first-person community post.
    Falls back to a safe minimal variant if the AI call fails."""
    try:
        details = data.get('additional_details') or ''
        time_hint = data.get('incident_time') or ''
        prompt = (
            "Rewrite the following incident description into a first-person, supportive community post. "
            "Use plain, respectful language, keep it anonymous (do not include names, addresses, phone numbers, or employers). "
            "Avoid placeholders like [Your Name]. Focus on what I experienced, how it affected me, and what support I’m seeking. "
            "Target length: 80-130 words in one paragraph.\n\n"
            f"Incident type: {data.get('incident_type') or 'Not specified'}\n"
            f"Who involved: {data.get('who_involved') or 'Not specified'}\n"
            f"Location: {data.get('location') or 'Not specified'}\n"
            f"Approx. time: {time_hint or 'Not specified'}\n"
            f"Impacts: {', '.join(data.get('impact') or []) or 'Not specified'}\n"
            f"Additional details: {details}\n\n"
            "Original summary (third-person):\n" + (ai_summary or '') + "\n\n"
            "Now produce the final first-person post starting with 'I' or 'Today I', without headings:"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 300}
        }
        response = requests.post(
            GEMINI_API_URL,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                return result['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as _:
        pass
    # Fallback minimal first-person version
    base = ai_summary or 'I experienced an incident and wanted to share here for support.'
    return f"I wanted to share what happened: {base}"[:1200]

@bp.route('/summary')
def show_summary():
    ai_summary = session.get('ai_summary', '')
    report_data = session.get('report_data', {})
    return render_template('report_summary.html', 
                         summary=ai_summary, 
                         report_data=report_data)

@bp.route('/download_report')
def download_report():
    """Download AI report as text file"""
    # Check if specific report_id is requested
    report_id = request.args.get('report_id')
    
    if report_id:
        # Download specific report from database
        report = IncidentReport.query.get(report_id)
        if not report:
            flash('Report not found.', 'danger')
            return redirect(url_for('main.my_reports'))
        
        # Verify user owns this report
        if session.get('user_id') != report.user_id:
            flash('Access denied.', 'danger')
            return redirect(url_for('main.my_reports'))
        
        ai_summary = report.ai_summary or 'No summary available'
        report_date = report.created_at.strftime('%Y-%m-%d %H:%M:%S')
    else:
        # Use session data (for immediate download after submission)
        ai_summary = session.get('ai_summary', 'No report available')
        report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create text content
    content = f"""INCIDENT REPORT SUMMARY
Generated: {report_date}

{ai_summary}

---
CONFIDENTIAL REPORT - SafeSpace Women's Safety Application
"""
    
    # Create response with file download
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = f'attachment; filename=incident_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    return response

@bp.route('/final_actions', methods=['POST'])
def final_actions():
    report_to_police = request.form.get('report_police') == 'yes'
    post_to_community = request.form.get('post_community') == 'yes'
    report_id = session.get('report_id')
    
    if report_id:
        # Update the report in database
        incident_report = IncidentReport.query.get(report_id)
        if incident_report:
            incident_report.report_to_police = report_to_police
            incident_report.posted_to_community = post_to_community
            
            if post_to_community:
                # Get user info if logged in
                user_id = session.get('user_id')
                username = None
                is_anonymous = True
                
                if user_id:
                    user = User.query.get(user_id)
                    if user:
                        # Check if user wants to post anonymously (from form or default setting)
                        raw_choice = request.form.get('post_as_anonymous')
                        if raw_choice is None:
                            # No checkbox submitted; fall back to user's default preference
                            is_anonymous = user.default_anonymous
                        else:
                            is_anonymous = (raw_choice == 'on')
                        
                        if not is_anonymous:
                            username = user.username
                
                # Prefer user-provided community story; else generate first-person from AI summary
                provided_story = (request.form.get('community_story') or '').strip()
                story_text = provided_story if provided_story else generate_first_person_story(session.get('report_data', {}), incident_report.ai_summary)

                # Create community post
                community_post = CommunityPost(
                    report_id=incident_report.id,
                    user_id=user_id,
                    username=username,
                    is_anonymous=is_anonymous,
                    story=story_text
                )
                db.session.add(community_post)
                
                if is_anonymous:
                    flash('Your story has been posted anonymously to the community support forum.', 'success')
                else:
                    flash(f'Your story has been posted to the community support forum as {username}.', 'success')
            
            db.session.commit()
    
    if report_to_police:
        flash('Important: Please visit your nearest police station or call emergency services. Your report has been saved and can be downloaded.', 'info')
    
    return redirect(url_for('main.community_support'))

@bp.route('/community')
def community_support():
    # Get all active community posts
    posts = CommunityPost.query.filter_by(is_active=True).order_by(CommunityPost.created_at.desc()).all()
    
    # Format posts for template
    formatted_posts = []
    for post in posts:
        # Determine category from report
        location = post.report.location if post.report else 'other'
        category_map = {
            'workplace': 'Workplace',
            'school': 'School/College',
            'home': 'Home',
            'public_place': 'Public Place',
            'online': 'Online'
        }
        category = category_map.get(location, 'General')
        
        # Get comments for this post
        comments = Comment.query.filter_by(post_id=post.id, is_active=True).order_by(Comment.created_at.asc()).all()
        formatted_comments = []
        for comment in comments:
            formatted_comments.append({
                'id': comment.id,
                'user_id': comment.user_id,
                'username': comment.username,
                'is_anonymous': comment.is_anonymous,
                'text': comment.text,
                'timestamp': comment.created_at
            })
        
        formatted_posts.append({
            'id': post.id,
            'user_id': post.user_id,
            'username': post.username,
            'is_anonymous': post.is_anonymous,
            'summary': post.story,
            'category': category,
            'timestamp': post.created_at,
            'reactions': {
                'support': post.support_count,
                'hug': post.hug_count,
                'solidarity': post.solidarity_count
            },
            'comments': formatted_comments
        })
    
    return render_template('community_support.html', posts=formatted_posts)

# ---------------- SOS Center API Endpoints -----------------

@bp.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve files from the uploads directory (limited to app/uploads)."""
    base_dir = os.path.join('app', 'uploads')
    return send_from_directory(base_dir, filename, as_attachment=False)

@bp.route('/api/sos', methods=['POST'])
def api_sos():
    """Log an SOS event to database and JSON file, return an sosId."""
    _ensure_dirs()
    _, logs_dir, _ = _ensure_dirs()
    payload = request.get_json(silent=True) or {}
    
    # Create database entry
    sos_alert = SOSAlert(
        user_id=session.get('user_id'),
        trigger_time=datetime.utcnow(),
        trigger_method=payload.get('triggeredBy', 'button'),
        latitude=payload.get('location', {}).get('latitude'),
        longitude=payload.get('location', {}).get('longitude'),
        battery_level=payload.get('battery'),
        is_active=True
    )
    
    try:
        db.session.add(sos_alert)
        db.session.commit()
        sos_id = sos_alert.id
        
        # Send SMS alerts to emergency contacts
        if session.get('user_id'):
            user = User.query.get(session['user_id'])
            contacts = EmergencyContact.query.filter_by(user_id=session['user_id'], is_active=True).all()
            
            if contacts:
                # Generate tracking link
                tracking_link = f"{request.host_url}track/{sos_id}"
                user_name = user.username if user else 'User'
                battery = payload.get('battery', 'Unknown')
                user_phone = user.phone if user else None
                
                # Send SMS alerts using user's own phone number
                contacts_notified = send_sms_alert(contacts, user_name, tracking_link, battery, user_phone)
                sos_alert.contacts_notified = contacts_notified
                sos_alert.notification_sent_at = datetime.utcnow()
                db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in SOS logging: {e}")
        # Fallback to timestamp-based ID
        sos_id = int(datetime.utcnow().timestamp() * 1000)
    
    # Also log to JSON for backup
    entry = {
        'user': payload.get('user') or (session.get('username') or 'Anonymous'),
        'time': payload.get('time') or datetime.utcnow().isoformat(),
        'intensity': payload.get('intensity', 'N/A'),
        'location': payload.get('location', {}),
        'contactsNotified': payload.get('contactsNotified', 0),
        'triggeredBy': payload.get('triggeredBy', 'Manual'),
        'sosId': sos_id
    }
    _append_json(os.path.join(logs_dir, 'sos_log.json'), entry)
    return jsonify({'status': 'SOS logged', 'sosId': sos_id})

@bp.route('/api/sos-live', methods=['POST'])
def api_sos_live():
    _ensure_dirs()
    _, logs_dir, _ = _ensure_dirs()
    payload = request.get_json(silent=True) or {}
    entry = {
        'sosId': payload.get('sosId'),
        'latitude': payload.get('latitude'),
        'longitude': payload.get('longitude'),
        'timestamp': payload.get('timestamp') or datetime.utcnow().isoformat()
    }
    _append_json(os.path.join(logs_dir, 'live_locations_log.json'), entry)
    return jsonify({'status': 'Live location logged'})

@bp.route('/api/shake-intensity', methods=['POST'])
def api_shake_intensity():
    _ensure_dirs()
    _, logs_dir, _ = _ensure_dirs()
    payload = request.get_json(silent=True) or {}
    entry = {
        'intensity': payload.get('intensity', '0'),
        'acceleration': payload.get('acceleration', {}),
        'timestamp': payload.get('timestamp') or datetime.utcnow().isoformat()
    }
    path = os.path.join(logs_dir, 'shake_intensity_log.json')
    # Keep only last 1000 entries
    try:
        if os.path.exists(path):
            data = json.load(open(path, 'r', encoding='utf-8'))
        else:
            data = []
    except Exception:
        data = []
    data.append(entry)
    if len(data) > 1000:
        data = data[-1000:]
    json.dump(data, open(path, 'w', encoding='utf-8'), indent=2)
    return jsonify({'status': 'Shake intensity logged'})

@bp.route('/api/alert-police', methods=['POST'])
def api_alert_police():
    _ensure_dirs()
    _, logs_dir, _ = _ensure_dirs()
    payload = request.get_json(silent=True) or {}
    entry = {
        'sosId': payload.get('sosId'),
        'location': payload.get('location', {}),
        'details': payload.get('details', {}),
        'timestamp': datetime.utcnow().isoformat()
    }
    _append_json(os.path.join(logs_dir, 'alerts_log.json'), entry)
    return jsonify({'status': 'Police alert logged'})

@bp.route('/api/broadcast', methods=['POST'])
def api_broadcast():
    _ensure_dirs()
    _, logs_dir, _ = _ensure_dirs()
    payload = request.get_json(silent=True) or {}
    entry = {
        'sosId': payload.get('sosId'),
        'location': payload.get('location', {}),
        'message': payload.get('message', ''),
        'timestamp': datetime.utcnow().isoformat()
    }
    _append_json(os.path.join(logs_dir, 'alerts_log.json'), entry)
    return jsonify({'status': 'Broadcast logged'})

@bp.route('/api/upload-recording', methods=['POST'])
def api_upload_recording():
    _ensure_dirs()
    base_dir, logs_dir, rec_dir = _ensure_dirs()
    if 'recording' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['recording']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    # Secure file name and ensure extension
    filename = secure_filename(file.filename)
    # Default to .webm if no extension
    if '.' not in filename:
        filename += '.webm'
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    unique = f"{ts}_{filename}"
    save_path = os.path.join(rec_dir, unique)
    file.save(save_path)

    # Log metadata
    meta = {
        'filename': unique,
        'originalName': file.filename,
        'size': os.path.getsize(save_path),
        'mimetype': file.mimetype,
        'uploadTime': datetime.utcnow().isoformat(),
        'sosId': request.form.get('sosId'),
        'user': session.get('username') or 'Anonymous',
        'duration': request.form.get('duration')
    }
    _append_json(os.path.join(logs_dir, 'recordings_log.json'), meta)
    file_url = url_for('main.serve_uploads', filename=f"sos/recordings/{unique}")
    return jsonify({'status': 'Recording uploaded', 'fileUrl': file_url, 'recordingData': meta})

@bp.route('/api/recordings')
def api_recordings():
    _, logs_dir, _ = _ensure_dirs()
    path = os.path.join(logs_dir, 'recordings_log.json')
    if not os.path.exists(path):
        return jsonify([])
    return send_from_directory(logs_dir, 'recordings_log.json', as_attachment=False)

@bp.route('/api/download-sos')
def dl_sos():
    _, logs_dir, _ = _ensure_dirs()
    path = os.path.join(logs_dir, 'sos_log.json')
    if not os.path.exists(path):
        return jsonify({'error': 'No SOS logs found'}), 404
    return send_from_directory(logs_dir, 'sos_log.json', as_attachment=True)

@bp.route('/api/download-shake-intensity')
def dl_shake():
    _, logs_dir, _ = _ensure_dirs()
    path = os.path.join(logs_dir, 'shake_intensity_log.json')
    if not os.path.exists(path):
        return jsonify({'error': 'No shake intensity logs found'}), 404
    return send_from_directory(logs_dir, 'shake_intensity_log.json', as_attachment=True)

@bp.route('/api/download-recordings')
def dl_recordings():
    _, logs_dir, _ = _ensure_dirs()
    path = os.path.join(logs_dir, 'recordings_log.json')
    if not os.path.exists(path):
        return jsonify({'error': 'No recordings logs found'}), 404
    return send_from_directory(logs_dir, 'recordings_log.json', as_attachment=True)

@bp.route('/api/lock-recording', methods=['POST'])
def api_lock_recording():
    """Mark a recording as locked in recordings_log.json to prevent cleanup."""
    _ensure_dirs()
    _, logs_dir, _ = _ensure_dirs()
    payload = request.get_json(silent=True) or {}
    filename = payload.get('filename')
    sos_id = payload.get('sosId')
    path = os.path.join(logs_dir, 'recordings_log.json')
    if not os.path.exists(path):
        return jsonify({'error': 'No recordings log'}), 404
    try:
        data = json.load(open(path, 'r', encoding='utf-8'))
    except Exception:
        data = []
    updated = False
    for r in data:
        if (filename and r.get('filename') == filename) or (sos_id and str(r.get('sosId')) == str(sos_id)):
            r['locked'] = True
            updated = True
    json.dump(data, open(path, 'w', encoding='utf-8'), indent=2)
    if updated:
        return jsonify({'status': 'Recording(s) locked'})
    return jsonify({'error': 'Recording not found'}), 404

@bp.route('/api/react/<int:post_id>/<reaction_type>', methods=['POST'])
def add_reaction(post_id, reaction_type):
    """Add a reaction to a post"""
    if reaction_type not in ['support', 'hug', 'solidarity']:
        return jsonify({'success': False, 'error': 'Invalid reaction type'}), 400
    
    post = CommunityPost.query.get(post_id)
    if post:
        if reaction_type == 'support':
            post.support_count += 1
        elif reaction_type == 'hug':
            post.hug_count += 1
        elif reaction_type == 'solidarity':
            post.solidarity_count += 1
        
        db.session.commit()
        count = getattr(post, f'{reaction_type}_count')
        return jsonify({'success': True, 'count': count})
    
    return jsonify({'success': False, 'error': 'Post not found'}), 404

@bp.route('/api/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    """Add a comment to a post"""
    data = request.get_json()
    comment_text = data.get('comment', '').strip()
    is_anonymous = data.get('is_anonymous', True)
    
    if not comment_text:
        return jsonify({'success': False, 'error': 'Comment cannot be empty'}), 400
    
    post = CommunityPost.query.get(post_id)
    if post:
        # Get user info if logged in
        user_id = session.get('user_id')
        username = None
        
        if user_id and not is_anonymous:
            user = User.query.get(user_id)
            if user:
                username = user.username
        
        # Create comment
        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            username=username,
            is_anonymous=is_anonymous,
            text=comment_text
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # Return comment data
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'user_id': user_id,
                'username': username if not is_anonymous else None,
                'is_anonymous': is_anonymous,
                'text': comment_text,
                'timestamp': comment.created_at.isoformat() if hasattr(comment, 'created_at') else None
            }
        })
    
    return jsonify({'success': False, 'error': 'Post not found'}), 404

@bp.route('/api/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    """Delete a community post (only by the post author)"""
    print(f"[DELETE POST] Request received for post_id: {post_id}")
    print(f"[DELETE POST] Session logged_in: {session.get('logged_in')}")
    print(f"[DELETE POST] Session user_id: {session.get('user_id')}")
    
    if not session.get('logged_in'):
        print("[DELETE POST] User not logged in")
        return jsonify({'success': False, 'error': 'You must be logged in to delete posts'}), 401
    
    post = CommunityPost.query.get(post_id)
    if not post:
        print(f"[DELETE POST] Post {post_id} not found")
        return jsonify({'success': False, 'error': 'Post not found'}), 404
    
    # Check if the current user is the post author
    user_id = session.get('user_id')
    print(f"[DELETE POST] Post user_id: {post.user_id}, Session user_id: {user_id}")
    
    if post.user_id != user_id:
        print(f"[DELETE POST] Authorization failed - post.user_id={post.user_id} != session.user_id={user_id}")
        return jsonify({'success': False, 'error': 'You can only delete your own posts'}), 403
    
    try:
        # Delete all comments associated with this post
        Comment.query.filter_by(post_id=post_id).delete()
        
        # Mark the post as inactive (soft delete) rather than hard delete
        post.is_active = False
        db.session.commit()
        
        print(f"[DELETE POST] Post {post_id} successfully deleted")
        return jsonify({'success': True, 'message': 'Post deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"[DELETE POST] Error: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to delete post: {str(e)}'}), 500

@bp.route('/support-chat')
def support_chat():
    """AI support chatbot for emotional support and safety guidance"""
    return render_template('support_chat.html')

@bp.route('/api/chat', methods=['POST'])
def chat_api():
    """Handle chat messages and return AI responses"""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
    
    # Build empathetic AI prompt
    system_context = """You are SafeSpace Support, a compassionate AI counselor specialized in women's safety and emotional support. Your role:

1. EMOTIONAL SUPPORT:
   - Listen with empathy and validate feelings
   - Provide comfort during difficult times
   - Never judge or minimize experiences
   - Use warm, caring language

2. SAFETY GUIDANCE:
   - Offer practical safety tips for various situations
   - Suggest de-escalation strategies
   - Provide resources and helpline information
   - Help create safety plans

3. EMPOWERMENT:
   - Encourage seeking help when needed
   - Reinforce that what happened is not their fault
   - Build confidence and resilience
   - Respect their choices and autonomy

4. BOUNDARIES:
   - You're not a replacement for professional therapy or emergency services
   - For immediate danger, always advise calling 181 (Women Helpline) or 100 (Police)
   - For serious trauma, recommend professional counseling
   - Keep responses concise (3-5 sentences usually)

Respond with empathy, practical advice, and hope. Be a supportive friend."""

    prompt = f"""{system_context}

User: {user_message}

Response (be warm, supportive, and helpful):"""
    
    try:
        # Call Gemini API
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.8,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 400
            }
        }
        
        response = requests.post(
            GEMINI_API_URL,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
                return jsonify({
                    'success': True,
                    'message': ai_response.strip()
                })
            else:
                return jsonify({
                    'success': False,
                    'message': "I'm here for you, but I'm having trouble responding right now. Please try again or call 181 for immediate support."
                }), 500
        else:
            return jsonify({
                'success': False,
                'message': "I'm experiencing technical difficulties. Please call 181 (Women Helpline) for immediate support."
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'message': "The response is taking longer than expected. Please try again or call 181 for immediate help."
        }), 500
    except Exception as e:
        print(f"Chat API Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': "I'm here to help, but I'm having technical issues. Please call 181 (Women Helpline) for support."
        }), 500

# ============ SAFE ROUTES FEATURE ============
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt, atan2
import hashlib
import os
from .route_optimizer import (
    calculate_route_hash,
    get_route_from_osrm,
    calculate_composite_score,
    calculate_route_safety_comprehensive,
)

# Load safety data (robust to current working directory)
try:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(APP_DIR, 'data')
    crime_data = pd.read_csv(os.path.join(DATA_DIR, 'bangalore_crimes.csv'))
    lighting_data = pd.read_csv(os.path.join(DATA_DIR, 'bangalore_lighting.csv'))
    population_data = pd.read_csv(os.path.join(DATA_DIR, 'bangalore_population.csv'))
    print(f"✅ Loaded {len(crime_data)} crime records")
    print(f"✅ Loaded {len(lighting_data)} lighting points")
    print(f"✅ Loaded {len(population_data)} population points")
except Exception as e:
    print(f"⚠️ Warning: Could not load safety data: {e}")
    crime_data = pd.DataFrame()
    lighting_data = pd.DataFrame()
    population_data = pd.DataFrame()

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    try:
        lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return c * 6371
    except:
        return 0

def calculate_crime_exposure(lat, lon, radius=0.003):
    """Calculate crime exposure at a location"""
    try:
        if crime_data.empty:
            return 0
        nearby_crimes = crime_data[
            (abs(crime_data['Latitude'] - lat) < radius) &
            (abs(crime_data['Longitude'] - lon) < radius)
        ]
        return len(nearby_crimes)
    except:
        return 0


@bp.route('/safe-routes')
def safe_routes():
    """Render full-featured Safe Routes page with navbar."""
    return render_template('safe_routes_container.html')

@bp.route('/safe-routes-standalone')
def safe_routes_standalone():
    """Standalone Safe Routes UI mapped to full feature template."""
    return render_template('safe_routes_FULL.html')

@bp.route('/safe-routes-full')
def safe_routes_full():
     """Full-featured safe routes with turn-by-turn navigation, animations, saved locations, ratings, and themes"""
     return render_template('safe_routes_FULL.html')

@bp.route('/api/geocode')
def api_geocode():
    """Geocode an address to coordinates"""
    address = request.args.get('address', '')
    
    if not address:
        return jsonify({'error': 'Address is required'}), 400
    
    try:
        # Use OpenStreetMap Nominatim for geocoding
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': f"{address}, Bangalore, Karnataka, India",
            'format': 'json',
            'limit': 1
        }
        headers = {'User-Agent': 'SafeSpace-WomenSafety/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return jsonify({
                    'success': True,
                    'coordinates': [lat, lon],
                    'display_name': data[0].get('display_name', address)
                })
        
        return jsonify({'error': 'Location not found'}), 404
        
    except Exception as e:
        print(f"Geocoding error: {e}")
        return jsonify({'error': 'Geocoding failed'}), 500

# (duplicate /api/calculate-route removed)

@bp.route('/api/calculate-route', methods=['POST'])
def api_calculate_route():
    """Calculate safe route between two points"""
    try:
        data = request.get_json()
        start_lat = float(data.get('start_lat'))
        start_lon = float(data.get('start_lon'))
        end_lat = float(data.get('end_lat'))
        end_lon = float(data.get('end_lon'))
        preferences = data.get('preferences', {})
        
        # Get route from OSRM (OpenStreetMap Routing Machine)
        url = f'http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}'
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'true'
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            return jsonify({'error': 'Route calculation failed'}), 500
        
        route_data = response.json()
        
        if 'routes' not in route_data or len(route_data['routes']) == 0:
            return jsonify({'error': 'No route found'}), 404
        
        # Extract route coordinates
        route = route_data['routes'][0]
        geometry = route['geometry']['coordinates']
        
        # Convert from [lon, lat] to [lat, lon]
        route_coords = [[coord[1], coord[0]] for coord in geometry]
        
        # Calculate distance and time
        distance_km = route['distance'] / 1000
        duration_min = int(route['duration'] / 60)
        
        # Calculate safety using comprehensive scoring
        safety_details = calculate_route_safety_comprehensive(
            route_coords,
            crime_data,
            lighting_data,
            population_data,
            preferences={},
        )
        # Scale to 0-10 for backward compatibility with simple UI
        safety_score = None
        if safety_details and 'safety_score' in safety_details:
            safety_score = round(safety_details['safety_score'] / 10.0, 1)
        
        return jsonify({
            'success': True,
            'route': route_coords,
            'distance': round(distance_km, 2),
            'time': duration_min,
            'safety_score': safety_score
        })
        
    except Exception as e:
        print(f"Route calculation error: {e}")
        return jsonify({'error': 'Failed to calculate route'}), 500

# ---------- Additional Safe Routes API Endpoints ----------

@bp.route('/api/search-place')
def api_search_place():
    """Autocomplete search using Nominatim."""
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify({'success': True, 'results': []})
    try:
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': f"{q}, Bangalore, Karnataka, India",
            'format': 'json',
            'limit': 5,
            'addressdetails': 1
        }
        headers = {'User-Agent': 'SafeSpace-WomenSafety/1.0'}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        items = []
        if resp.status_code == 200:
            data = resp.json()
            for d in data:
                try:
                    items.append({
                        'display_name': d.get('display_name'),
                        'lat': float(d['lat']),
                        'lon': float(d['lon'])
                    })
                except Exception:
                    continue
        return jsonify({'success': True, 'results': items})
    except Exception as e:
        print(f"search-place error: {e}")
        return jsonify({'success': True, 'results': []})

@bp.route('/api/reverse-geocode')
def api_reverse_geocode():
    lat = request.args.get('lat'); lon = request.args.get('lon')
    try:
        latf = float(lat); lonf = float(lon)
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400
    try:
        url = 'https://nominatim.openstreetmap.org/reverse'
        params = {
            'lat': latf,
            'lon': lonf,
            'format': 'json'
        }
        headers = {'User-Agent': 'SafeSpace-WomenSafety/1.0'}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({'success': True, 'address': data.get('display_name')})
        return jsonify({'success': False, 'error': 'Reverse geocoding failed'}), 500
    except Exception as e:
        print(f"reverse-geocode error: {e}")
        return jsonify({'success': False, 'error': 'Reverse geocoding failed'}), 500

def _filter_bbox(df, bbox):
    if df is None or df.empty:
        return df
    try:
        min_lat, min_lon, max_lat, max_lon = map(float, bbox)
        return df[(df['Latitude'] >= min_lat) & (df['Latitude'] <= max_lat) & (df['Longitude'] >= min_lon) & (df['Longitude'] <= max_lon)]
    except Exception:
        return df

@bp.route('/api/crime-heatmap')
def api_crime_heatmap():
    bbox = request.args.get('bbox')
    df = crime_data
    if bbox:
        parts = bbox.split(',')
        if len(parts) == 4:
            df = _filter_bbox(df, parts)
    if df is None or df.empty:
        return jsonify({'success': True, 'total_crimes': 0, 'data': []})
    # Convert to list of [lat, lon]
    subset = df[['Latitude','Longitude']].head(2000)
    data = [[float(row['Latitude']), float(row['Longitude'])] for _, row in subset.iterrows()]
    return jsonify({'success': True, 'total_crimes': len(data), 'data': data})

@bp.route('/api/lighting-heatmap')
def api_lighting_heatmap():
    bbox = request.args.get('bbox')
    df = lighting_data
    if bbox:
        parts = bbox.split(',')
        if len(parts) == 4:
            df = _filter_bbox(df, parts)
    if df is None or df.empty:
        return jsonify({'success': True, 'total_locations': 0, 'data': []})
    subset = df[['Latitude','Longitude','lighting_score']].head(5000)
    data = [[float(r['Latitude']), float(r['Longitude']), float(r['lighting_score'])] for _, r in subset.iterrows()]
    return jsonify({'success': True, 'total_locations': len(data), 'data': data})

@bp.route('/api/population-heatmap')
def api_population_heatmap():
    bbox = request.args.get('bbox')
    df = population_data
    if bbox:
        parts = bbox.split(',')
        if len(parts) == 4:
            df = _filter_bbox(df, parts)
    if df is None or df.empty:
        return jsonify({'success': True, 'total_locations': 0, 'data': []})
    cols = ['Latitude','Longitude','population_density','traffic_level','is_main_road']
    subset = df[cols].head(5000)
    data = [
        [float(r['Latitude']), float(r['Longitude']), float(r['population_density']), float(r['traffic_level']), int(r['is_main_road'])]
        for _, r in subset.iterrows()
    ]
    return jsonify({'success': True, 'total_locations': len(data), 'data': data})

@bp.route('/api/optimize-route', methods=['POST'])
def api_optimize_route():
    """Enhanced route optimization with crime-aware waypoint generation and comprehensive safety scoring"""
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
        
        # Validate coordinates within Bangalore
        BANGALORE_BOUNDS = {
            'min_lat': 12.704192, 'max_lat': 13.173706,
            'min_lon': 77.269876, 'max_lon': 77.850066
        }
        
        if not all(BANGALORE_BOUNDS['min_lat'] <= lat <= BANGALORE_BOUNDS['max_lat'] and
                   BANGALORE_BOUNDS['min_lon'] <= lon <= BANGALORE_BOUNDS['max_lon']
                   for lat, lon in [(start_lat, start_lon), (end_lat, end_lon)]):
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
                    safety = calculate_route_safety_comprehensive(
                        route_data['route'],
                        crime_data,
                        lighting_data,
                        population_data,
                        preferences,
                    )
                    if safety:
                        route_data.update(safety)
                        route_data['route_hash'] = route_hash
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
                    
                    # Validate waypoint coordinates
                    if not (BANGALORE_BOUNDS['min_lat'] <= wp_lat <= BANGALORE_BOUNDS['max_lat'] and
                            BANGALORE_BOUNDS['min_lon'] <= wp_lon <= BANGALORE_BOUNDS['max_lon']):
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
                                safety = calculate_route_safety_comprehensive(
                                    route_data['route'],
                                    crime_data,
                                    lighting_data,
                                    population_data,
                                    preferences,
                                )
                                if safety:
                                    route_data.update(safety)
                                    route_data['route_hash'] = route_hash
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
        
        print("\n--- Phase 3: Preference-Based Scoring (with personalization) ---")
        
        # Load user preferences if available and override incoming weights
        liked_hashes = set()
        try:
            if session.get('user_id'):
                prefs = UserPreference.query.filter_by(user_id=session['user_id']).first()
                if prefs:
                    preferences['safety_weight'] = float(prefs.safety_weight or preferences['safety_weight'])
                    preferences['distance_weight'] = float(prefs.distance_weight or preferences['distance_weight'])
                    preferences['prefer_main_roads'] = bool(prefs.prefer_main_roads)
                    preferences['prefer_well_lit'] = bool(prefs.prefer_well_lit)
                    preferences['prefer_populated'] = bool(prefs.prefer_populated)
                # Collect positively-rated route hashes for a small history bonus
                rows = RouteFeedback.query.filter_by(user_id=session['user_id']).order_by(RouteFeedback.created_at.desc()).limit(100).all()
                liked_hashes = {r.route_hash for r in rows if (r.rating or 0) >= 4 and r.route_hash}
        except Exception as _:
            pass

        for route in all_routes:
            base = calculate_composite_score(route, preferences)
            bonus = 0.0
            try:
                if route.get('route_hash') and route['route_hash'] in liked_hashes:
                    bonus += 0.15
                # Proximity bonus for similar endpoints to previously liked routes
                if session.get('user_id'):
                    prox = db.session.execute(text(
                        """
                        SELECT 1 FROM route_feedback
                         WHERE user_id = :uid AND rating >= 4
                           AND ABS(start_lat - :slat) < 0.01 AND ABS(start_lon - :slon) < 0.01
                           AND ABS(end_lat - :elat) < 0.01 AND ABS(end_lon - :elon) < 0.01
                         LIMIT 1
                        """),
                        {
                            'uid': session['user_id'],
                            'slat': float(start_lat), 'slon': float(start_lon),
                            'elat': float(end_lat), 'elon': float(end_lon)
                        }
                    ).first()
                    if prox:
                        bonus += 0.1
            except Exception:
                pass
            route['composite_score'] = base + bonus
        
        all_routes.sort(key=lambda x: x['composite_score'], reverse=True)
        
        final_routes = all_routes[:7]
        print(f"Final routes to display: {len(final_routes)}")
        
        # Track which categories have been assigned to avoid duplicates
        assigned_categories = set()
        min_distance = min(r['distance_km'] for r in final_routes)
        min_crime = min(r['crime_density'] for r in final_routes)
        
        for idx, route in enumerate(final_routes):
            route['rank'] = idx + 1
            route['is_recommended'] = (idx == 0)
            
            # Assign unique category to each route
            if idx == 0:
                category = 'best'
                description = 'Best match for your preferences'
            elif 'safest' not in assigned_categories and route['crime_density'] <= 1.5 and route['max_crime_exposure'] <= 3:
                category = 'safest'
                description = 'Safest route (avoids crime hotspots)'
            elif 'fastest' not in assigned_categories and route['distance_km'] <= min_distance * 1.02:
                category = 'fastest'
                description = 'Shortest distance'
            elif 'main_roads' not in assigned_categories and route['main_road_percentage'] >= 70:
                category = 'main_roads'
                description = 'Uses main roads'
            elif 'well_lit' not in assigned_categories and route.get('lighting_score', 0) >= 7.5:
                category = 'well_lit'
                description = 'Well-lit route'
            elif 'populated' not in assigned_categories and route.get('population_score', 0) >= 6:
                category = 'populated'
                description = 'Populated areas'
            else:
                # Give each route a unique descriptor based on its characteristics
                if route['crime_density'] <= min_crime * 1.2:
                    category = 'low_crime'
                    description = f"Low crime route ({route['crime_density']:.1f} incidents)"
                elif route['distance_km'] <= min_distance * 1.15:
                    category = 'short'
                    description = f"Short route ({route['distance_km']:.1f}km)"
                elif route['main_road_percentage'] >= 50:
                    category = 'major_roads'
                    description = f"Major roads ({route['main_road_percentage']:.0f}%)"
                else:
                    category = 'alternative'
                    description = f"Alternative route"
            
            assigned_categories.add(category)
            route['category'] = category
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
                reasons.append(f"Crime density: {route['crime_density']:.1f}")
            
            if route.get('max_crime_exposure', 0) <= 2:
                reasons.append("No crime hotspots")
            elif route.get('max_crime_exposure', 0) <= 5:
                reasons.append("Minimal crime exposure")
            else:
                reasons.append(f"Max crime exposure: {route['max_crime_exposure']:.0f}")
            
            if route.get('main_road_percentage', 0) > 70:
                reasons.append(f"{route['main_road_percentage']:.0f}% main roads")
            if route.get('lighting_score', 0) > 7.5:
                reasons.append("Well-lit area")
            if route.get('population_score', 0) > 6:
                reasons.append("Populated area")
            
            route['reasons'] = reasons
            
            if route.get('max_crime_exposure', 0) > 8 or route.get('crime_density', 0) > 5:
                route['warning'] = "High crime exposure"
            elif route.get('max_crime_exposure', 0) > 5 or route.get('crime_density', 0) > 3:
                route['warning'] = "Moderate crime exposure"
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
        print(f"\nError in route optimization: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/health')
def api_health():
    return jsonify({
        'success': True,
        'services': {
            'osrm': 'online',
            'nominatim': 'online'
        },
        'data': {
            'crimes': 0 if crime_data is None else len(crime_data),
            'lighting': 0 if lighting_data is None else len(lighting_data),
            'population': 0 if population_data is None else len(population_data)
        }
    })

@bp.route('/api/rate-route', methods=['POST'])
def api_rate_route():
    try:
        payload = request.get_json() or {}
        route_id = payload.get('route_id')
        rating = int(payload.get('rating', 0))
        feedback = (payload.get('feedback') or '').strip()
        if not route_id or rating < 1 or rating > 5:
            return jsonify({'success': False, 'error': 'Invalid rating'}), 400
        os.makedirs('app/data', exist_ok=True)
        path = 'app/data/route_ratings.json'
        data = []
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = []
        entry = {
            'route_id': route_id,
            'rating': rating,
            'feedback': feedback,
            'timestamp': datetime.utcnow().isoformat()
        }
        data.append(entry)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return jsonify({'success': True})
    except Exception as e:
        print(f"rate-route error: {e}")
        return jsonify({'success': False, 'error': 'Failed to save rating'}), 500

@bp.route('/api/user-feedback', methods=['POST'])
def api_user_feedback():
    """Store user route feedback and update preferences for personalization."""
    try:
        payload = request.get_json(silent=True) or {}
        rating = int(payload.get('rating', 0))
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'error': 'Rating must be 1-5'}), 400

        user_id = session.get('user_id')
        rh = payload.get('route_hash')
        start_lat = float(payload.get('start_lat')) if payload.get('start_lat') is not None else None
        start_lon = float(payload.get('start_lon')) if payload.get('start_lon') is not None else None
        end_lat = float(payload.get('end_lat')) if payload.get('end_lat') is not None else None
        end_lon = float(payload.get('end_lon')) if payload.get('end_lon') is not None else None
        feedback_text = (payload.get('feedback') or '').strip()

        rf = RouteFeedback(
            user_id=user_id,
            route_hash=rh,
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            rating=rating,
            feedback=feedback_text,
            safety_score=payload.get('safety_score'),
            lighting_score=payload.get('lighting_score'),
            population_score=payload.get('population_score'),
            main_road_percentage=payload.get('main_road_percentage'),
            distance_km=payload.get('distance_km'),
            duration_min=payload.get('duration_min')
        )
        db.session.add(rf)

        # Update preferences gently if logged in
        if user_id:
            prefs = UserPreference.query.filter_by(user_id=user_id).first()
            if not prefs:
                prefs = UserPreference(user_id=user_id)
                db.session.add(prefs)

            if rating >= 4:
                # Nudge toward safety
                sw = min(0.95, (prefs.safety_weight or 0.7) + 0.05)
                dw = max(0.05, 1.0 - sw)
                prefs.safety_weight, prefs.distance_weight = sw, dw
                # Infer toggles
                try:
                    if (payload.get('lighting_score') or 0) >= 6:
                        prefs.prefer_well_lit = True
                    if (payload.get('population_score') or 0) >= 6:
                        prefs.prefer_populated = True
                    if (payload.get('main_road_percentage') or 0) >= 50:
                        prefs.prefer_main_roads = True
                except Exception:
                    pass
            elif rating <= 2:
                # Relax safety slightly
                sw = max(0.4, (prefs.safety_weight or 0.7) - 0.05)
                dw = min(0.6, 1.0 - sw)
                prefs.safety_weight, prefs.distance_weight = sw, dw

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"user-feedback error: {e}")
        return jsonify({'success': False, 'error': 'Failed to save feedback'}), 500

@bp.route('/api/route-feedback', methods=['POST'])
def api_route_feedback():
    """
    Comprehensive route safety feedback endpoint
    Accepts detailed feedback about route safety features and user experience
    """
    try:
        payload = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['route_from', 'route_to', 'travel_time', 'safety_rating', 'recommendation']
        for field in required_fields:
            if not payload.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate safety rating
        safety_rating = int(payload.get('safety_rating', 0))
        if safety_rating < 1 or safety_rating > 5:
            return jsonify({'success': False, 'error': 'Safety rating must be between 1 and 5'}), 400
        
        # Ensure data directory exists
        os.makedirs('app/data', exist_ok=True)
        feedback_file = 'app/data/route_feedback.json'
        
        # Load existing feedback
        feedback_data = []
        if os.path.exists(feedback_file):
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    feedback_data = json.load(f)
            except Exception as e:
                print(f"Error loading feedback data: {e}")
                feedback_data = []
        
        # Create feedback entry
        feedback_entry = {
            'route_id': payload.get('route_id', f'route_{len(feedback_data) + 1}'),
            'route_from': payload.get('route_from'),
            'route_to': payload.get('route_to'),
            'travel_time': payload.get('travel_time'),
            'safety_rating': safety_rating,
            'safety_features': payload.get('safety_features', []),
            'recommendation': payload.get('recommendation'),
            'suggested_improvements': payload.get('suggested_improvements', ''),
            'safety_concerns': payload.get('safety_concerns', ''),
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': session.get('user_id', 'anonymous')
        }
        
        # Append new feedback
        feedback_data.append(feedback_entry)
        
        # Save to file
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Route feedback saved: {feedback_entry['route_from']} → {feedback_entry['route_to']} (Rating: {safety_rating}/5)")
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!',
            'feedback_id': len(feedback_data)
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Invalid rating value'}), 400
    except Exception as e:
        print(f"❌ route-feedback error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to save feedback'}), 500

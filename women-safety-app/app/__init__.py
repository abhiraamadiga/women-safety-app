from flask import Flask
from datetime import datetime
import os
from sqlalchemy import text
from dotenv import load_dotenv

def create_app():
    # Load environment variables from .env if present
    try:
        load_dotenv()
    except Exception:
        pass
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production-2024'
    app.config['UPLOAD_FOLDER'] = 'app/uploads/evidence'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'women_safety.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    from app.models import db
    from app.auth_models import User  # Import User model
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
        # Lightweight migration: add new columns if missing (SQLite only)
        try:
            from app.models import db as _db
            with _db.engine.connect() as conn:
                # Migrate users table
                res = conn.execute(text("PRAGMA table_info(users);") )
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
                existing_cols_c = {row[1]: row[2] for row in res4}  # col_name: col_type
                
                # If user_id exists but is wrong type (VARCHAR instead of INTEGER), we need to handle it
                if 'user_id' in existing_cols_c and 'VARCHAR' in existing_cols_c['user_id']:
                    # SQLite doesn't support column type changes, so we'd need to recreate table
                    # For now, just add missing columns
                    pass
                
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
            # Ignore migration issues silently in dev
            print(f"Migration warning: {e}")
            pass
    
    from app import routes
    app.register_blueprint(routes.bp)
    
    # Context processor to add today's date
    @app.context_processor
    def inject_today():
        return {'today': datetime.now().strftime('%Y-%m-%d')}
    
    return app

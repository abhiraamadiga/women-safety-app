"""
Database migration script to add new columns and tables for Emergency SOS features
Run this script to update your existing database with new schema changes
"""

from app import create_app
from app.models import db
from app.auth_models import User
from app.models import EmergencyContact, SOSAlert
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        print("Starting database migration...")
        
        # Get database connection
        connection = db.engine.connect()
        
        try:
            # Step 1: Add emergency_pin_hash column to users table if it doesn't exist
            print("\n1. Checking users table...")
            try:
                connection.execute(text("SELECT emergency_pin_hash FROM users LIMIT 1"))
                print("   ✓ emergency_pin_hash column already exists")
            except Exception:
                print("   → Adding emergency_pin_hash column...")
                connection.execute(text("ALTER TABLE users ADD COLUMN emergency_pin_hash VARCHAR(200)"))
                connection.commit()
                print("   ✓ emergency_pin_hash column added")
            
            # Step 2: Create emergency_contacts table if it doesn't exist
            print("\n2. Checking emergency_contacts table...")
            try:
                connection.execute(text("SELECT * FROM emergency_contacts LIMIT 1"))
                print("   ✓ emergency_contacts table already exists")
            except Exception:
                print("   → Creating emergency_contacts table...")
                connection.execute(text("""
                    CREATE TABLE emergency_contacts (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        phone VARCHAR(20) NOT NULL,
                        relationship VARCHAR(50) NOT NULL,
                        priority INTEGER DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY(user_id) REFERENCES users (id)
                    )
                """))
                connection.commit()
                print("   ✓ emergency_contacts table created")
            
            # Step 3: Create sos_alerts table if it doesn't exist
            print("\n3. Checking sos_alerts table...")
            try:
                connection.execute(text("SELECT * FROM sos_alerts LIMIT 1"))
                print("   ✓ sos_alerts table already exists")
            except Exception:
                print("   → Creating sos_alerts table...")
                connection.execute(text("""
                    CREATE TABLE sos_alerts (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        trigger_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        trigger_method VARCHAR(50) DEFAULT 'button',
                        latitude FLOAT,
                        longitude FLOAT,
                        location_accuracy FLOAT,
                        is_active BOOLEAN DEFAULT 1,
                        resolved_at DATETIME,
                        resolution_pin_verified BOOLEAN DEFAULT 0,
                        audio_recording_url VARCHAR(500),
                        video_recording_url VARCHAR(500),
                        contacts_notified INTEGER DEFAULT 0,
                        notification_sent_at DATETIME,
                        battery_level INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users (id)
                    )
                """))
                connection.commit()
                print("   ✓ sos_alerts table created")
            
            print("\n" + "="*60)
            print("✅ Database migration completed successfully!")
            print("="*60)
            print("\nYou can now:")
            print("  • Log in to your account")
            print("  • Add emergency contacts")
            print("  • Use the SOS Center features")
            print("  • Mark as safe with PIN")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            connection.rollback()
            raise
        finally:
            connection.close()

if __name__ == '__main__':
    migrate_database()

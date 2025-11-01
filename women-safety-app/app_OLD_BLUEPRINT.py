from app import create_app
import os

if __name__ == '__main__':
    app = create_app()
    # Use 0.0.0.0 to allow access from any device on the network
    use_ssl = os.environ.get('FLASK_SSL', '0') in ('1', 'true', 'True')
    ssl_ctx = 'adhoc' if use_ssl else None
    # Note: 'adhoc' requires the 'cryptography' package. If unavailable, the server will error.
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000, ssl_context=ssl_ctx)

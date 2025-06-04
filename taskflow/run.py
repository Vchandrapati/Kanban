from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Use PORT environment variable for deployment platforms
    port = int(os.environ.get('PORT', 5000))
    # Bind to 0.0.0.0 for deployment, disable debug in production
    app.run(host='0.0.0.0', port=port, debug=False)
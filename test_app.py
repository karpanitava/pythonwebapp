import pytest
from app import app as flask_app # Import your Flask app instance

# We use a pytest fixture to set up a test client
@pytest.fixture
def client():
    # Use Flask's testing environment configuration
    flask_app.config['TESTING'] = True
    # Change the DB URI to an in-memory SQLite DB for testing
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
    
    with flask_app.test_client() as client:
        # Before each test, ensure the database is clean
        from app import db, User, Lecture
        with flask_app.app_context():
            db.create_all() # Create tables
            
            # Optionally add a test user/lecture if needed for specific tests
            
        yield client # The test runs here

        # After each test, clean up the database
        with flask_app.app_context():
            db.drop_all()

# --- Simple Unit Tests ---

def test_login_page_loads(client):
    """Test that the login page loads successfully."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Login or Register to CICDClouds" in response.data

def test_dashboard_requires_login(client):
    """Test that the dashboard redirects to login if user is not logged in."""
    # Since dashboard has @login_required, it should redirect (status 302)
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302 
    # Check that the redirection points to /login
    assert '/login' in response.headers['Location']

# NOTE: For full functional tests (Selenium), you would run the app in a separate process
# and write tests that interact with the live server.
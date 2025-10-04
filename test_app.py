import pytest
from app import app as flask_app  # Import your Flask app instance

# --- Pytest Fixture for Test Client ---
@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with flask_app.test_client() as client:
        from app import db, User, Lecture
        with flask_app.app_context():
            db.create_all()

        yield client  # Run tests here

        with flask_app.app_context():
            db.drop_all()

# --- Unit Tests ---

def test_login_page_loads(client):
    """Test that the login page loads successfully."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Login or Register to CICDClouds" in response.data

def test_dashboard_requires_login(client):
    """Test that the dashboard redirects to login if user is not logged in."""
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_login_with_valid_user(client):
    from app import db, User
    with flask_app.app_context():
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()

        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)

        assert b'Logged in successfully!' in response.data

# --- Optional: Selenium Functional Tests ---
# NOTE: These should be placed in a separate file like test_ui.py
# and run against a live server instance.

# from selenium import webdriver
 def test_login_page_ui():
     driver = webdriver.Chrome()
     driver.get("http://localhost:5000/login")
     assert "Login or Register to CICDClouds" in driver.page_source
     driver.quit()

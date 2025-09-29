from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Configuration
app = Flask(__name__)
# Set a secret key for session management (CHANGE THIS IN A REAL APP!)
app.config['SECRET_KEY'] = 'your_super_secret_key_for_cicdclouds' 
# SQLite database path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cicdclouds.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # The function name for the login route

# --- User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    # This function tells Flask-Login how to find a user by their ID
    return User.query.get(int(user_id))

# --- Database Models ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    notes = db.relationship('Note', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Lecture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    video_url = db.Column(db.String(255), nullable=False)
    notes = db.relationship('Note', backref='lecture', lazy='dynamic')

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lecture.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

# ----------------------------------------------------
# 📌 APPLICATION ROUTES - DEFINED BEFORE APP RUN 📌
# ----------------------------------------------------

# --- Authentication Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    if user:
        flash('Username already exists. Please choose a different one.', 'error')
        return redirect(url_for('login'))
    
    # Create the new user
    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required 
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# --- Core Application Routes ---

@app.route('/')
@app.route('/dashboard')
@login_required 
def dashboard():
    # Fetch all available lectures from the database
    lectures = Lecture.query.all()
    # Pass the list of lectures to the template
    return render_template('dashboard.html', lectures=lectures)

@app.route('/lecture/<int:lecture_id>', methods=['GET', 'POST'])
@login_required
def lecture_view(lecture_id):
    # Get the specific lecture, or show a 404 error if it doesn't exist
    lecture = Lecture.query.get_or_404(lecture_id)
    
    # Handle saving a new note
    if request.method == 'POST':
        note_content = request.form.get('note_content')
        if note_content:
            # Create a new note linked to the current user and the current lecture
            new_note = Note(
                content=note_content,
                user_id=current_user.id,
                lecture_id=lecture.id
            )
            db.session.add(new_note)
            db.session.commit()
            flash('Your note has been saved!', 'success')
            # Redirect to the same page to prevent form resubmission
            return redirect(url_for('lecture_view', lecture_id=lecture.id))
        else:
            flash('Note content cannot be empty.', 'error')

    # Fetch all notes written by the CURRENT USER for this SPECIFIC LECTURE
    user_notes = Note.query.filter_by(user_id=current_user.id, lecture_id=lecture.id).order_by(Note.timestamp.desc()).all()
    
    return render_template('lecture_view.html', lecture=lecture, notes=user_notes)

# ----------------------------------------------------

# --- Database Setup Helper ---
def initialize_db():
    # A simple function to create the tables and add some initial data
    with app.app_context():
        db.create_all()

        # Add some sample lectures if they don't exist
        if Lecture.query.count() == 0:
            lecture1 = Lecture(title="Lecture 1: Intro to CI/CD", video_url="https://www.youtube.com/embed/dQw4w9WgXcQ") 
            lecture2 = Lecture(title="Lecture 2: Docker Basics", video_url="https://www.youtube.com/embed/g8f0bF-0z2k") 
            db.session.add_all([lecture1, lecture2])
            db.session.commit()
            print("Added sample lectures.")

if __name__ == '__main__':
    # Initialize the database before running the app
    initialize_db()
    app.run(debug=True)
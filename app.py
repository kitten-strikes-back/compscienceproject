from bs4 import BeautifulSoup
import requests

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
books = []
# Fetch book data from the website
response = requests.get('https://www.oclc.org/en/worldcat/library100/top500.html')
soup = BeautifulSoup(response.text, 'html.parser')
all_td_tags = soup.find_all('td', class_='ti')

for td in all_td_tags:
    a = td.find('a')
    text = a.text
    books.append(text)  # Append the text of each <a> tag to the books list
# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'th1s_1s_a_s3cr3t_k3y'  #Not secure, just for demonstration purposes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable track modifications for performance

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login page if not logged in

# Define User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/')
def index():
    return render_template('index.html')
    

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Query the database for a user with the submitted username
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:  # Replace with hashed password check if using hashing
            login_user(user)  
            return redirect(url_for('home')) 

    return render_template('login.html')

# Route for the signup page

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Check if the user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('signup'))

        # Try creating a new user
        try:
            new_user = User(username=username, password=password, role=role)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            return '<html><script>alert(That username is already taken. Please try again.)</script></html>'
        except Exception:
            return redirect(url_for('signup'))

    return render_template('signup.html')
@app.route('/home', methods=['GET', 'POST'])
@login_required  # Ensures only logged-in users can access this page
def home():
    global books  # Use the global books list
    if request.method == 'POST':
        booklist = request.form.getlist('book')  # List of books selected by the user
        print("Selected books:", booklist)
        print()
        print("Current user:", current_user.username)
        print()
        print("User role:", current_user.role)
        print
        print('Please give permission for these selected books for their respective users.')
    return render_template('home.html', username=current_user.username, role=current_user.role, allbooks=books)  # Pass the current user's username and role to the template
# Route for logging out
@app.route('/logout')
@login_required
def logout():
    logout_user()  
    return redirect(url_for('login')) 

if __name__ == '__main__':
    # Use app.app_context() to work inside the application context
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True, host='0.0.0.0', port=8080)  # Run the app

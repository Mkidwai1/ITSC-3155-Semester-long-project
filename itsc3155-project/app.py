from flask import Flask, request, render_template, redirect, session, flash, url_for 
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'itis3155proj'

# Define your Canvas instance URL here
CANVAS_INSTANCE_URL = 'https://uncc.instructure.com'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    canvas_api_key = db.Column(db.String(255))
    course_codes_list = db.Column(db.String(255))  # New field for storing course codes

    def __init__(self, email, password, name, canvas_api_key):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.canvas_api_key = canvas_api_key

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        canvas_api_key = request.form.get('canvas_api_key')  

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists. If this was you, please log in.')
            return redirect(url_for('register'))

        new_user = User(email=email, password=password, name=name, canvas_api_key=canvas_api_key)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            session['user_name'] = user.name
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Email or Password. Please try again.')
            
    return render_template('login.html')
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        
        if request.method == 'POST':
            course_codes = request.form.get('course_codes')
            course_codes_list = [code.strip() for code in course_codes.split(',') if code.strip()]
            user.course_codes_list = ','.join(course_codes_list)
            db.session.commit()
            flash('Course codes updated successfully. You can now view your Canvas calendar.', 'success')  # Modified to include additional instruction
            return redirect(url_for('dashboard'))  # Redirect back to the dashboard to show the flash message

        return render_template('dashboard.html', user=user)
    
    return redirect(url_for('login'))

@app.route('/canvas-calendar')
def canvas_calendar():
    if 'email' not in session:
        flash('Please log in to view the Canvas calendar.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    course_codes = user.course_codes_list.split(',') if user.course_codes_list else []
    calendar_events = fetch_canvas_calendar_events(user.id, course_codes)
    print("Calendar events in route:", calendar_events)  
    return render_template('canvas_calendar.html', events=calendar_events)

def fetch_canvas_calendar_events(user_id, course_codes):
    user_instance = User.query.get(user_id)
    if not user_instance:
        flash('User not found.')
        return []

    if not user_instance.canvas_api_key:
        flash("Canvas API key is missing.")
        return []

    headers = {
        'Authorization': f'Bearer {user_instance.canvas_api_key}'
    }

    all_events = []

    for code in course_codes:
        context_code = f'course_{code}'
        params = {
            'type': 'event',
            'context_codes[]': context_code,
            'start_date': '2024-03-01',
            'end_date': '2024-03-31'
        }

        events_response = requests.get(
            f'{CANVAS_INSTANCE_URL}/api/v1/calendar_events',
            headers=headers,
            params=params
        )

        if events_response.status_code == 200:
            events = events_response.json()
            all_events.extend(events)
        else:
            flash(f'Failed to fetch events for course {code}: {events_response.reason}')

    return all_events

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/todo')
def todo():
    return render_template('todo.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/logout')
def logout():
    session.pop('email', None)  # Remove user email from session
    session.pop('name', None)   # Remove user name from session
    flash('You have been logged out.')
    return redirect(url_for('index'))

from flask import Flask, request, render_template, redirect, session, flash, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import bcrypt
from random import randint


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config["MAIL_SERVER"]='smtp.gmail.com'
app.config["MAIL_PORT"]=465
app.config["MAIL_USERNAME"]='noreply.progresspixel@gmail.com'  # Use environment variables for sensitive info
app.config['MAIL_PASSWORD']='yhue qgef inkn ctwg'  # Use environment variables
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
mail=Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
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
    avatar = db.Column(db.String(255))

    def __init__(self, email, password, name, canvas_api_key, avatar):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.canvas_api_key = canvas_api_key
        self.avatar = avatar

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
        # Retrieve form data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        canvas_api_key = request.form.get('canvas_api_key')
        avatar = request.form.get('avatar', 'pixelBoy.png')  # Set default avatar if none selected
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists. Please log in.')
            return redirect(url_for('register'))

        # Create new user with either selected avatar or default
        new_user = User(email=email, password=password, name=name, canvas_api_key=canvas_api_key, avatar=avatar)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Logic to authenticate the user
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.check_password(request.form.get('password')):
            session['email'] = user.email
            session['user_name'] = user.name
            session['user_avatar'] = user.avatar if user.avatar else 'pixelBoy.png' # Assuming user.avatar stores the filename
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Email or Password. Please try again.')
    return render_template('login.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        
        if request.method == 'POST':
            course_codes = request.form.get('course_codes')
            course_codes_list = [code.strip() for code in course_codes.split(',') if code.strip()]
            user.course_codes_list = ','.join(course_codes_list)
            db.session.commit()
            flash('Course codes updated successfully. You can now view your Canvas calendar.', 'success')  # Modified to include additional instruction
            return redirect(url_for('dashboard'))  # Redirect back to the dashboard to show the flash message

        return render_template('settings.html', user=user)
    
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
import requests

def fetch_canvas_calendar_events(user_id, course_codes):
    user_instance = db.session.get(User, user_id)
    if not user_instance:
        flash('User not found.')
        return []

    if not user_instance.canvas_api_key:
        flash("Canvas API key is missing.")
        return []

    headers = {'Authorization': f'Bearer {user_instance.canvas_api_key}'}

    all_items = []  # This will include both events and assignments

    # Fetch events
    for code in course_codes:
        context_code = f'course_{code}'
        params = {
            'context_codes[]': context_code,
        }

        try:
            events_response = requests.get(
                f'{CANVAS_INSTANCE_URL}/api/v1/calendar_events',
                headers=headers,
                params=params
            )
            events_response.raise_for_status()
            events = events_response.json()
            all_items.extend(events)  # Add events to all_items
        except requests.RequestException as e:
            flash(f'Failed to fetch events for course {code}: {str(e)}')

    # Fetch assignments for each course and treat them as calendar events
    for code in course_codes:
        try:
            assignments_response = requests.get(
                f'{CANVAS_INSTANCE_URL}/api/v1/courses/{code}/assignments',
                headers=headers,
                params={'start_date': '2024-03-01', 'end_date': '2024-03-31', 'per_page': 100}
            )
            assignments_response.raise_for_status()
            assignments = assignments_response.json()

            for assignment in assignments:
                # Convert assignment to a calendar event-like structure if necessary
                assignment_event = {
                    'title': assignment['name'],
                    'start_at': assignment['due_at'],
                    'description': assignment.get('description', 'No description'),
                    'url': assignment['html_url'],
                    'type': 'assignment'
                }
                all_items.append(assignment_event)

        except requests.RequestException as e:
            flash(f'Failed to fetch assignments for course {code}: {str(e)}')

    return all_items


#changing/customizing avatar to be implemented
@app.route('/update_avatar', methods=['POST'])
def update_avatar():
    if 'email' not in session:
        flash("Please log in to update your avatar.")
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        flash("User not found.")
        return redirect(url_for('login'))

    avatar = request.form.get('avatar')
    if avatar:
        user.avatar = avatar
        db.session.commit()
        flash("Your avatar has been updated.")
    else:
        flash("No avatar selected.")

    return redirect(url_for('dashboard'))

@app.route('/todo')
def todo():
    return render_template('todo.html')

@app.route('/shop')
def shop():
    if 'email' not in session:
        flash('Please log in to access the shop.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    # Example structure for shop items. This should ideally come from your database.
    shop_items = {
        'avatars': [
            {'name': 'PixelGirl', 'price': 0, 'img': 'pixelGirl.png', 'unlocked': True},
            {'name': 'PixelBoy', 'price': 0, 'img': 'pixelBoy.png', 'unlocked': True},
            # Add other avatars with their prices here
        ],
        'themes': [
            # Placeholder for themes
        ]
    }

    return render_template('shop.html', user=user, shop_items=shop_items)


@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        flash('Please log in to access the dashboard.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    return render_template('dashboard.html', user=user)

@app.route('/logout')
def logout():
    session.pop('email', None)  # Remove user email from session
    session.pop('name', None)   # Remove user name from session
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            otp = randint(000000,999999)
            session['otp'] = otp
            session['email_for_otp'] = email  # Save email in session to use in the validation step
            
            msg = Message(subject='OTP for Password Reset', sender='your_email@example.com', recipients=[email])
            msg.body = f'Your OTP is {otp}'
            mail.send(msg)
            
            flash('An OTP has been sent to your email. Please check to verify.')
            return redirect(url_for('verify_otp'))
        else:
            flash('No matching account found. Please check your details.', 'warning')
    return render_template('forgot.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        if 'otp' in session and int(user_otp) == session['otp']:
            email = session.pop('email_for_otp', None)
            session.pop('otp', None)  # Clear the OTP from the session
            
            user = User.query.filter_by(email=email).first()
            if user:
                db.session.delete(user)
                db.session.commit()
                flash('OTP verified. Your account has been reset. Please register again.', 'success')
                return redirect(url_for('register'))
            else:
                flash('Session error. Please try the reset process again.', 'danger')
                return redirect(url_for('forgot'))
        else:
            flash('Invalid OTP. Please try again.')
            return render_template('verify_otp.html')
    return render_template('verify_otp.html')



if __name__ == '__main__':
    app.run(debug=True)


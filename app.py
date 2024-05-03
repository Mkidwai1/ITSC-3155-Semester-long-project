from flask import Flask, request, render_template, redirect, session, flash, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import bcrypt
from random import randint
from datetime import date, timedelta, datetime
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask import jsonify

shop_items = {
    'avatars': [
        {'item_id': 1, 'name': 'PixelGirl', 'price': 10, 'img': 'pixelGirl.png', 'unlocked': True},
        {'item_id': 2, 'name': 'PixelBoy', 'price': 10, 'img': 'pixelBoy.png', 'unlocked': True},
    ],
}

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
socketio = SocketIO(app)
online_users = set()

# Define your Canvas instance URL here
CANVAS_INSTANCE_URL = 'https://uncc.instructure.com'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    canvas_api_key = db.Column(db.String(255))
    course_codes_list = db.Column(db.String(255))
    avatar = db.Column(db.String(255))
    coins = db.Column(db.Integer)
    color_picker_unlocked = db.Column(db.Boolean, default=False)
    
    user_items = db.relationship('UserItem', backref='user', lazy=True, cascade="all, delete, delete-orphan")

    def __init__(self, email, password, name, canvas_api_key, avatar, coins, color_picker_unlocked=False):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.canvas_api_key = canvas_api_key
        self.avatar = avatar
        self.coins = coins
        self.color_picker_unlocked = color_picker_unlocked  # Initialize with default value


    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    img = db.Column(db.String(255))

    def __repr__(self):
        return f'<Item {self.name}>'


class UserItem(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    unlocked = db.Column(db.Boolean, default=False)
    
    item = db.relationship('Item', backref='user_items', lazy=True)

class Todo(db.Model):
    assignmentID = db.Column(db.Integer, primary_key=True)
    assignmentName = db.Column(db.String(255))

    def __repr__(self):
        return self.assignmentName

def seed_items():
    # Clear existing items to prevent duplication
    db.session.query(Item).delete()

    # Define the items to add
    items = [
        Item(name='PixelGirl', price=0, img='pixelGirl.png'),
        Item(name='PixelBoy', price=0, img='pixelBoy.png'),
        Item(name='Blue Boy', price=100, img='blueBoy.png'),
        Item(name='Pink Girl', price=100, img='pink1Girl.png'),
        Item(name='Gray Boy', price=100, img='grayBoy.png'),
        Item(name='Green Girl', price=100, img='greenGirl.png'),
        Item(name='Pink 2Girl', price=100, img='pink2Girl.png'),
    ]

    # Add new items to the database
    db.session.bulk_save_objects(items)
    db.session.commit()
    print("Database seeded with initial items.")

with app.app_context():
    db.create_all()
    seed_items()


@app.route('/')
def home():
    if 'email' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        canvas_api_key = request.form.get('canvas_api_key')
        avatar = request.form.get('avatar', 'pixelBoy.png')  # Set default avatar if none selected
        coins = 0
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists. Please log in.')
            return redirect(url_for('register'))

        # Create new user with either selected avatar or default
        new_user = User(email=email, password=password, name=name, canvas_api_key=canvas_api_key, avatar=avatar, coins=coins)
        db.session.add(new_user)
        db.session.commit()

        # Automatically unlock default avatars for the new user
        default_avatars = Item.query.filter(Item.img.in_(['pixelBoy.png', 'pixelGirl.png'])).all()
        for avatar_item in default_avatars:
            user_item = UserItem(user_id=new_user.id, item_id=avatar_item.id, unlocked=True)
            db.session.add(user_item)
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
            session['user_coins'] = user.coins
            session['unlocked_items'] = [item['item_id'] for item in shop_items['avatars'] if item['unlocked']]
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
            flash('Course codes updated successfully.', 'success')
            return redirect(url_for('dashboard'))

        # Fetching the current user's course codes to display
        course_codes = user.course_codes_list.split(',') if user.course_codes_list else []
        return render_template('settings.html', user=user, course_codes=course_codes)
    
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
    return render_template('canvas_calendar.html', events=calendar_events, user=user)
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


# #changing/customizing avatar to be implemented
# @app.route('/update_avatar', methods=['POST'])
# def update_avatar():
#     if 'email' not in session:
#         flash("Please log in to update your avatar.")
#         return redirect(url_for('login'))

#     user = User.query.filter_by(email=session['email']).first()
#     if not user:
#         flash("User not found.")
#         return redirect(url_for('login'))

#     avatar = request.form.get('avatar')
#     if avatar:
#         user.avatar = avatar
#         db.session.commit()
#         flash("Your avatar has been updated.")
#         return jsonify({'success': True, 'message': 'Avatar updated successfully!'})
#     else:
#         flash("No avatar selected.")
#         return jsonify({'success': False, 'message': 'No avatar selected.'})
    
    
    
@app.route('/set-avatar', methods=['POST'])
def set_avatar():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Please log in first.'}), 401

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    item_id = request.form.get('item_id', type=int)
    if not item_id:
        return jsonify({'success': False, 'message': 'Invalid item.'}), 400

    user_item = UserItem.query.filter_by(user_id=user.id, item_id=item_id).first()
    if not user_item or not user_item.unlocked:
        return jsonify({'success': False, 'message': 'Avatar not unlocked or does not exist.'}), 404

    # Set the new avatar image path
    item = Item.query.get(item_id)
    if item:
        user.avatar = item.img
        db.session.commit()
        return jsonify({'success': True, 'message': 'Avatar updated successfully!', 'new_avatar': url_for('static', filename='images/' + item.img)})
    else:
        return jsonify({'success': False, 'message': 'Item not found.'}), 404

@app.route('/delete/<int:assignmentID>')
def delete(assignmentID):
    user = User.query.filter_by(email=session['email']).first()
    assignment_to_delete = Todo.query.get_or_404(assignmentID)
    try:
        if(user.coins == None):
            user.coins = 0
        user.coins = user.coins + 10
        db.session.delete(assignment_to_delete)
        db.session.commit()
        return redirect('/todo')
    except:
        return 'Could not delete assignment'


@app.route('/generateList')
def add():
    user = User.query.filter_by(email=session['email']).first()
    course_codes = user.course_codes_list.split(',') if user.course_codes_list else []
    calendar_events = fetch_canvas_calendar_events(user.id, course_codes)
    
    weekDays = []
    day = 1
    while(day <= 7) :
        weekDays.append(str(date.today() + timedelta(days=day))[0:10])
        day = day + 1

    months = []
    days = []   
    assignmentNames = []
    for events in calendar_events:
        duedate = str(events['start_at'])[0:10]
        if(weekDays.count(duedate) > 0):
            months.append(int(duedate[5:7]))
            days.append(int(duedate[8:10]))
            assignmentNames.append(str(events['title']))

    for i in range(len(assignmentNames)):
        if(Todo.query.get(i) != None):
            try:
                db.session.delete(Todo.query.get(i))
            except:
                return 'Could not clear table'
                
    for i in range(len(months)):
        for x in range(len(months)):
            if(months[i] < months[x]):
                m = months[i]
                n = assignmentNames[i]
                d = days[i]
                months[i] = months[x]
                months[x] = m
                assignmentNames[i] = assignmentNames[x]
                assignmentNames[x] = n
                days[i] = days[x]
                days[x] = d

    for i in range(len(days)):
        for x in range(len(days)):
            if(months[i] == months[x]):
                if(days[i] < days[x]): 
                    m = months[i]
                    n = assignmentNames[i]
                    d = days[i]
                    months[i] = months[x]
                    months[x] = m
                    assignmentNames[i] = assignmentNames[x]
                    assignmentNames[x] = n
                    days[i] = days[x]
                    days[x] = d
   
    for i in range(len(months)):
        currentYear = str(date.today())[0:4]
        stringDate = currentYear + "-" + str(months[i]) + "-" + str(days[i])
        dueDate = datetime.strptime(stringDate, "%Y-%m-%d")
        dueDate = dueDate - timedelta(days=1)
        dueMonth = dueDate.strftime("%b")
        newAssignment = Todo(assignmentID = i, assignmentName = assignmentNames[i] + " - Due " + dueMonth + " " + str(dueDate)[8:10])
        try:
            db.session.add(newAssignment)
            db.session.commit()
        except:
            return 'Could not create to do list'
        
    return redirect('/todo')

@app.route('/todo')
def todo():
    user = User.query.filter_by(email=session['email']).first()
    tasks = Todo.query.all()
    return render_template('todo.html', assignments = tasks, user=user)


@app.route('/shop')
def shop():
    if 'email' not in session:
        flash('Please log in to access the shop.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    # Fetch all items and check which ones are unlocked
    all_items = Item.query.all()
    unlocked_items = {ui.item.id for ui in user.user_items if ui.unlocked}  # use .all() to fetch items

    # Mark items as unlocked in the context sent to the template
    items_for_display = [{
        'id': item.id,
        'name': item.name,
        'img': item.img,
        'price': item.price,
        'unlocked': item.id in unlocked_items
    } for item in all_items]


    return render_template('shop.html', user=user, items=items_for_display)


@app.route('/inventory')
def inventory():
    if 'email' not in session:
        flash('Please log in to view your inventory.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    # Fetching user items that are unlocked
    user_items = UserItem.query.filter_by(user_id=user.id, unlocked=True).all()

    return render_template('shop.html', user=user, user_items=user_items)



@app.route('/buy-item', methods=['POST'])
def buy_item():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Please log in to make purchases.'}), 401

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    item_id = request.form.get('item_id', type=int)
    price = request.form.get('price', type=int)  # This should be validated or derived from the database
    item = Item.query.get(item_id)

    if not item:
        return jsonify({'success': False, 'message': 'Item not found.'}), 404
    if user.coins < item.price:
        return jsonify({'success': False, 'message': 'Not enough coins.'}), 400
    if UserItem.query.filter_by(user_id=user.id, item_id=item.id).first():
        return jsonify({'success': False, 'message': 'Item already purchased.'}), 400

    user.coins -= item.price
    new_user_item = UserItem(user_id=user.id, item_id=item.id, unlocked=True)
    db.session.add(new_user_item)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Purchase successful!', 'avatarUrl': url_for('static', filename='images/' + item.img)})

@app.route('/add-coins', methods=['POST'])
def add_coins():
    if 'email' not in session:
        flash("Please log in to update coins.")
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        flash("User not found.")
        return redirect(url_for('login'))

    # Add 100 coins for testing purposes
    user.coins += 100
    db.session.commit()

    flash("100 coins have been added to your account.")
    return redirect(url_for('shop'))  # Redirect back to the shop or wherever appropriate


@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        flash('Please log in to access the dashboard.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()
    assignments = Todo.query.all()
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    return render_template('dashboard.html', user=user, tasks = assignments)

@app.route('/logout')
def logout():
    session.pop('email', None)  # Remove user email from session
    session.pop('name', None)   # Remove user name from session
    flash('You have been logged out.')
    return redirect(url_for('dashboard'))

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

@socketio.on('connect')
def handle_connect():
    online_users.add(request.sid)
    emit('user_count', {'count': len(online_users)}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    online_users.remove(request.sid)
    emit('user_count', {'count': len(online_users)}, broadcast=True)
    
@app.route('/chat')
def chat():
    if 'email' not in session:
        flash('Please log in to access the chat.')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    return render_template('chat.html', user=user)

@socketio.on('message')
def handle_message(msg):
    send(msg, broadcast=True)
@app.route('/unlock-color-picker', methods=['POST'])
def unlock_color_picker():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Please log in to access this feature.'}), 401

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    if user.coins < 500:
        return jsonify({'success': False, 'message': 'Not enough coins to unlock the Color-Picker.'}), 400

    user.coins -= 500
    user.color_picker_unlocked = True
    db.session.commit()
    return jsonify({'success': True, 'message': 'Color-Picker unlocked successfully!'})

    
if __name__ == '__main__':
    socketio.run(app, debug=True)
    #app.run(debug=True)


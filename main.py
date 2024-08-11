from flask import Flask, request, jsonify,  render_template , redirect , url_for
import redis
import json
import time
from flask_wtf import FlaskForm
from wtforms import StringField, TimeField, SubmitField
from wtforms.validators import DataRequired
from flask_cors import CORS
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
CORS(app)

# Connect to Redis server
r = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/update-gps', methods=['POST'])
def update_gps():
    data = request.json
    latitude = data.get('lat')
    longitude = data.get('lng')

    if latitude and longitude:
        key = f"gps_data:{time.time()}"
        r.setex(key, 300, json.dumps({'latitude': latitude, 'longitude': longitude}))
        return jsonify({"status": "success", "message": "GPS data saved successfully", "redis_key": key}), 200
    else:
        return jsonify({"status": "error", "message": "Missing latitude or longitude"}), 400

@app.route('/latest-gps', methods=['GET'])
def get_latest_gps():
    keys = r.keys('gps_data:*')
    if not keys:
        return jsonify({"status": "error", "message": "No GPS data found"}), 404
    
    latest_key = max(keys)
    data = r.get(latest_key)
    if data:
        gps_data = json.loads(data.decode('utf-8'))
        return jsonify(gps_data), 200
    else:
        return jsonify({"status": "error", "message": "Unable to retrieve data"}), 500

@app.route('/map', methods=['GET'])
def map_view():
    # Get latest GPS data
    keys = r.keys('gps_data:*')
    if not keys:
        return "<h1>No GPS data available</h1>", 404
    
    latest_key = max(keys)
    data = r.get(latest_key)
    if data:
        gps_data = json.loads(data.decode('utf-8'))
        latitude = gps_data['latitude']
        longitude = gps_data['longitude']
    else:
        return "<h1>Unable to retrieve data</h1>", 500
  
    # HTML template for embedding OpenStreetMap with Leaflet
    return render_template('map.html')

class MedicineForm(FlaskForm):
    name = StringField('Medicine Name', validators=[DataRequired()])
    dosage = StringField('Dosage', validators=[DataRequired()])
    time = TimeField('Time', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Add Reminder')

@app.route('/medic', methods=['GET', 'POST'])
def index():
    form = MedicineForm()
    if form.validate_on_submit():
        # Create a unique key for each reminder
        key = f"reminder:{form.name.data}"
        reminder = {
            'name': form.name.data,
            'dosage': form.dosage.data,
            'time': form.time.data.strftime('%H:%M')
        }
        r.hmset(key, reminder)
        return redirect(url_for('index'))
    
    return render_template('medicineReminderForm.html', form=form)


def get_today_time(hour_minute_str):
    """Convert 'HH:MM' string to Unix timestamp for today."""
    now = datetime.now()
    today_time = datetime.strptime(hour_minute_str, '%H:%M').replace(year=now.year, month=now.month, day=now.day)
    return int(today_time.timestamp())

@app.route('/reminders', methods=['GET'])
def reminders():
    keys = r.keys('reminder:*')
    reminders = []
    current_time = int(time.time())

    # Fetch all reminders
    for key in keys:
        reminder = r.hgetall(key)
        try:
            reminder_time = get_today_time(reminder[b'time'].decode('utf-8'))  # Convert 'HH:MM' to today's Unix timestamp
        except ValueError:
            continue  # Skip any reminders with invalid time formats

        if reminder_time >= current_time:
            reminders.append({
                'name': reminder[b'name'].decode('utf-8'),
                'dosage': reminder[b'dosage'].decode('utf-8'),
                'time': reminder_time,
                'key': key
            })
        else:
            # If reminder time has passed, delete it
            r.delete(key)

    # Sort reminders by time (closest to now first)
    reminders.sort(key=lambda x: x['time'])

    # Get the closest reminder to the current time
    closest_reminder = reminders[0] if reminders else None

    if closest_reminder:
        # Return the closest reminder as JSON
        return jsonify({
            'name': closest_reminder['name'],
            'time': closest_reminder['time'],
            'dosage': closest_reminder['dosage']
        })
    else:
        # If no reminders, return an empty JSON object or a suitable message
        return jsonify({'message': 'No upcoming reminders'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

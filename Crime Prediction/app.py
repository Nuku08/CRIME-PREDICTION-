from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import json
import csv
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

@app.route('/predict', methods=['POST'])
def predict():
    location = request.form.get('location')
    time = request.form.get('time')
    csv_path = os.path.join('dataset', 'crime_data_with_coordinates.csv')
    results = []
    total_crimes = 0
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if location.lower() in row['District'].lower():
                    crime_count = 0
                    for k, v in row.items():
                        if k not in ['States/UTs','District','Year','latitude','longitude']:
                            try:
                                crime_count += int(v)
                            except:
                                continue
                    total_crimes += crime_count
                    lat = float(row['latitude'])
                    lon = float(row['longitude'])
                    results.append({'latitude': lat, 'longitude': lon, 'count': crime_count, 'district': row['District']})
        heatmap = [r for r in results if r['count'] > 5]
        summary = f"Total crimes in {location}: {total_crimes}. Probability of crime: {'High' if total_crimes > 20 else 'Medium' if total_crimes > 5 else 'Low'}"
    except Exception as e:
        heatmap = []
        summary = f"Error loading crime data: {e}"
    return jsonify({'heatmap': heatmap, 'summary': summary})

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users_path = os.path.join(os.path.dirname(__file__), 'users.json')
        try:
            with open(users_path, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except Exception:
            users = []
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')

        users_path = os.path.join(os.path.dirname(__file__), 'users.json')
        try:
            with open(users_path, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except Exception:
            users = []
        # Check if username already exists
        if any(u['username'] == username for u in users):
            return render_template('signup.html', error='Username already exists')
        users.append({'username': username, 'email': email, 'password': password})
        with open(users_path, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)
        flash('Signup successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        flash('Please log in to access the dashboard.')
        return redirect(url_for('login'))

    tips_path = os.path.join(os.path.dirname(__file__), 'incident_logs.json')
    try:
        with open(tips_path, 'r', encoding='utf-8') as f:
            tips = json.load(f)
    except Exception:
        tips = []

    heatmap = []
    summary = None
    csv_path = os.path.join('dataset', 'crime_data_with_coordinates.csv')
    if request.method == 'POST':
        location = request.form.get('location')
        time = request.form.get('time')
        results = []
        total_crimes = 0
        try:
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if location.lower() in row['District'].lower():
                        crime_count = 0
                        for k, v in row.items():
                            if k not in ['States/UTs','District','Year','latitude','longitude']:
                                try:
                                    crime_count += int(v)
                                except:
                                    continue
                        total_crimes += crime_count
                        lat = float(row['latitude'])
                        lon = float(row['longitude'])
                        results.append({'latitude': lat, 'longitude': lon, 'count': crime_count, 'district': row['District']})
            heatmap = [r for r in results if r['count'] > 5]
            summary = f"Total crimes in {location}: {total_crimes}. Probability of crime: {'High' if total_crimes > 20 else 'Medium' if total_crimes > 5 else 'Low'}"
        except Exception:
            summary = "Error loading crime data."
    else:
        # GET: show all districts
        try:
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    crime_count = 0
                    for k, v in row.items():
                        if k not in ['States/UTs','District','Year','latitude','longitude']:
                            try:
                                crime_count += int(v)
                            except Exception as e:
                                continue
                    try:
                        lat = float(row['latitude'])
                        lon = float(row['longitude'])
                        if crime_count > 5:
                            heatmap.append({'latitude': lat, 'longitude': lon, 'count': crime_count, 'district': row['District']})
                    except Exception as e:
                        print(f"Error parsing lat/lon for row: {row['District']}, error: {e}")
        except Exception as e:
            print(f"Error loading CSV: {e}")
            heatmap = []
            summary = "Error loading crime data. Please check the server logs and CSV file."

    return render_template('dashboard.html', tips=tips, heatmap=heatmap, summary=summary)

@app.route('/anonymous_tip', methods=['GET', 'POST'])
def anonymous_tip():
    tips_path = os.path.join(os.path.dirname(__file__), 'incident_logs.json')
    if request.method == 'POST':
        activity = request.form.get('activity')
        location = request.form.get('location')
        time = request.form.get('time')
        details = request.form.get('details')
        tip = {
            'activity': activity,
            'location': location,
            'time': time,
            'details': details
        }
        try:
            with open(tips_path, 'r', encoding='utf-8') as f:
                tips = json.load(f)
        except Exception:
            tips = []
        tips.append(tip)
        with open(tips_path, 'w', encoding='utf-8') as f:
            json.dump(tips, f, indent=2)
        flash('Anonymous tip submitted successfully!')
        # After submit, show the page again with updated tips
    try:
        with open(tips_path, 'r', encoding='utf-8') as f:
            tips = json.load(f)
    except Exception:
        tips = []
    return render_template('anonymous_tip.html', tips=tips)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
   
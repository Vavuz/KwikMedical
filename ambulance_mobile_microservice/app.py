from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import requests
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = 'secret_key'

HOSPITAL_SERVICE_URL = 'http://hospital_microservice:5000'

USERNAME = "ambulance"
PASSWORD = "password"

received_dispatches = {}

@app.route('/')
def login():
    return render_template('login.html', title="Ambulance Login")

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == USERNAME and password == PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid credentials, please try again.")
        return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', title="Ambulance Dashboard", received_dispatches=received_dispatches)

@app.route('/receive_medical_record', methods=['POST'])
def receive_medical_record():
    data = request.json
    patient_id = data.get("patient_id")

    if patient_id:
        received_dispatches[patient_id] = data
        flash(f"Medical record for patient {patient_id} received.")
        return jsonify({"status": "Medical record received", "data": data}), 200
    else:
        return jsonify({"status": "Patient ID missing in received data"}), 400

@app.route('/send_call_out_details/<int:patient_id>', methods=['POST'])
def send_call_out_details(patient_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    call_out_details = request.form.get('call_out_details')
    if not call_out_details:
        flash("Call-out details are required.")
        return redirect(url_for('dashboard'))

    data = {
        "patient_id": patient_id,
        "call_out_details": call_out_details
    }
    try:
        response = requests.post(f'{HOSPITAL_SERVICE_URL}/receive_call_out_details', json=data)
        if response.status_code == 200:
            flash("Call-out details sent successfully.")
        else:
            flash("Failed to send call-out details.")
    except requests.exceptions.RequestException as e:
        flash(f"Error communicating with Hospital Service: {e}")
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
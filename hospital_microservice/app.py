import random
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import requests
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = 'secret_key'

USERNAME = "hospital"
PASSWORD = "password"

AMBULANCE_SERVICE_URL = 'http://ambulance_mobile_microservice:5000'
PATIENT_DB_SERVICE_URL = 'http://patient_database_microservice:5000'
HEAD_OFFICE_SERVICE_URL = 'http://head_office_microservice:5000'

ready_dispatch_requests = {}
dispatched_requests = {}
call_out_updates = {}

@app.route('/')
def login():
    return render_template('login.html', title="Hospital Login")

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
    return render_template(
        'dashboard.html',
        title="Hospital Dashboard",
        ready_dispatch_requests=ready_dispatch_requests,
        dispatched_requests=dispatched_requests,
        call_out_updates=call_out_updates
    )


def get_patient_medical_record(patient_id):
    try:
        response = requests.get(f'{PATIENT_DB_SERVICE_URL}/get_patient/{patient_id}')
        if response.status_code == 200:
            return response.json().get('patient')
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving patient data: {e}")
    return None

@app.route('/prepare_dispatch', methods=['POST'])
def prepare_dispatch():
    data = request.json
    patient_id = data.get('patient_id')
    best_way = data.get('best_way')
    hospital_id = data.get('hospital_id')

    if patient_id and best_way and hospital_id:
        ready_dispatch_requests[patient_id] = {
            "patient_id": patient_id,
            "best_way": best_way,
            "hospital_id": hospital_id
        }
        return jsonify({"status": "Dispatch information received and ready"}), 200
    return jsonify({"error": "Incomplete dispatch data"}), 400

@app.route('/dispatch_ambulance/<int:patient_id>', methods=['POST'])
def dispatch_ambulance(patient_id):
    dispatch_data = ready_dispatch_requests.pop(patient_id, None)
    if not dispatch_data:
        flash("No dispatch information found for this patient.")
        return redirect(url_for('dashboard'))
    
    medical_record = get_patient_medical_record(patient_id)
    if not medical_record:
        flash("Failed to retrieve patient medical record.")
        return redirect(url_for('dashboard'))

    payload = {
        "patient_id": medical_record["id"],
        "name": medical_record.get("name"),
        "nhs_number": medical_record.get("nhs_number"),
        "address": medical_record.get("address"),
        "medical_condition": medical_record.get("medical_condition")
    }

    try:
        response = requests.post(f'{AMBULANCE_SERVICE_URL}/receive_medical_record', json=payload)
        if response.status_code == 200:
            dispatched_requests[patient_id] = dispatch_data
            flash("Ambulance dispatched and medical record sent.")
        else:
            ready_dispatch_requests[patient_id] = dispatch_data
            flash("Failed to dispatch ambulance. Please try again.")
    except requests.exceptions.RequestException as e:
        ready_dispatch_requests[patient_id] = dispatch_data
        flash(f"Communication error with Ambulance Service: {e}")
    return redirect(url_for('dashboard'))

@app.route('/receive_call_out_details', methods=['POST'])
def receive_call_out_details():
    data = request.json
    patient_id = data.get('patient_id')
    new_call_out_details = data.get('call_out_details')

    if not patient_id or not new_call_out_details:
        return jsonify({"error": "Patient ID or call-out details missing"}), 400

    try:
        response = requests.get(f'{PATIENT_DB_SERVICE_URL}/get_patient/{patient_id}')
        if response.status_code != 200:
            return jsonify({"error": f"Failed to fetch patient with ID {patient_id}"}), 404

        patient_data = response.json().get('patient')

        existing_call_out_details = patient_data.get('call_out_details', [])
        if not isinstance(existing_call_out_details, list):
            existing_call_out_details = []

        updated_call_out_details = existing_call_out_details + [new_call_out_details]

        update_payload = {
            "call_out_details": updated_call_out_details
        }
        update_response = requests.put(f'{PATIENT_DB_SERVICE_URL}/update_patient/{patient_id}', json=update_payload)

        if update_response.status_code == 200:
            call_out_updates[patient_id] = updated_call_out_details
            return jsonify({"status": "Call-out details updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to update patient call-out details"}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error communicating with Patient Database Service: {str(e)}"}), 500

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
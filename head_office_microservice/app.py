import random
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import requests
from config import Config
import json

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = 'secret_key'

USERNAME = "headoffice"
PASSWORD = "password"

PATIENT_DB_SERVICE_URL = 'http://patient_database_microservice:5000'
HOSPITAL_DB_SERVICE_URL = 'http://hospital_database_microservice:5000'
HOSPITAL_SERVICE_URL = 'http://hospital_microservice:5000'

patients_list = []
hospitals_list = []

def update_patients_list():
    global patients_list
    try:
        response = requests.get(f'{PATIENT_DB_SERVICE_URL}/get_patients')
        if response.status_code == 200:
            patients_list = response.json().get("patients", [])
        else:
            print("Failed to update patients list.")
    except requests.exceptions.RequestException as e:
        print(f"Error updating patients list: {e}")

def update_hospitals_list():
    global hospitals_list
    try:
        response = requests.get(f'{HOSPITAL_DB_SERVICE_URL}/get_hospitals')
        if response.status_code == 200:
            hospitals_list = response.json().get("hospitals", [])
        else:
            print("Failed to update hospitals list.")
    except requests.exceptions.RequestException as e:
        print(f"Error updating hospitals list: {e}")

@app.route('/view_patients', methods=['GET'])
def view_patients():
    try:
        response = requests.get(f'{PATIENT_DB_SERVICE_URL}/get_patients')
        patients = response.json().get("patients", [])
    except Exception as e:
        flash("Error fetching patients list.")
        patients = []

    for patient in patients:
        call_out_details = patient.get('call_out_details')
        if call_out_details:
            try:
                patient['call_out_details'] = json.loads(call_out_details)
                if not isinstance(patient['call_out_details'], list):
                    patient['call_out_details'] = ["Invalid call-out details format"]
            except (json.JSONDecodeError, TypeError):
                patient['call_out_details'] = ["Invalid call-out details format"]
        else:
            patient['call_out_details'] = ["No call-out details"]

    return render_template('view_patients.html', patients=patients)

@app.route('/view_hospitals', methods=['GET'])
def view_hospitals():
    try:
        response = requests.get(f'{HOSPITAL_DB_SERVICE_URL}/get_hospitals')
        hospitals = response.json().get("hospitals", [])
    except Exception as e:
        flash("Error fetching hospitals list.")
        hospitals = []
    return render_template('view_hospitals.html', hospitals=hospitals)

@app.route('/initiate_rescue_request', methods=['POST', 'GET'])
def initiate_rescue_request():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        if not patient_id:
            flash("Patient ID is required to initiate a rescue request.")
            return redirect(url_for('view_patients'))

        try:
            response = requests.post(f'{HOSPITAL_SERVICE_URL}/prepare_dispatch', json={'patient_id': patient_id})
            if response.status_code == 200:
                flash("Rescue request initiated successfully.")
            else:
                flash("Failed to initiate rescue request.")
        except Exception as e:
            flash("Error initiating rescue request.")
        return redirect(url_for('view_patients'))
    
    return redirect(url_for('dashboard'))

@app.route('/')
def login():
    return render_template('login.html', title="Head Office Login")

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
    update_patients_list()
    update_hospitals_list()
    return render_template('dashboard.html', patients=patients_list, hospitals=hospitals_list)

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        patient_data = request.form
        patient_payload = {
            "name": patient_data.get("name"),
            "nhs_number": patient_data.get("nhs_number"),
            "address": patient_data.get("address", ""),
            "medical_condition": patient_data.get("medical_condition", "")
        }
        try:
            response = requests.post(f'{PATIENT_DB_SERVICE_URL}/add_patient', json=patient_payload)
            if response.status_code == 201:
                update_patients_list()
                return redirect(url_for('view_patients'))
            else:
                return f"Failed to add patient: {response.text}", 500
        except requests.exceptions.RequestException as e:
            return f"Error communicating with Patient Database Service: {e}", 500
    return render_template('add_patient.html')

@app.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    if request.method == 'POST':
        name = request.form.get('name')
        nhs_number = request.form.get('nhs_number')
        address = request.form.get('address') or ""
        medical_condition = request.form.get('medical_condition') or ""

        updated_data = {
            "name": name,
            "nhs_number": nhs_number,
            "address": address,
            "medical_condition": medical_condition
        }
        response = requests.put(f'{PATIENT_DB_SERVICE_URL}/update_patient/{patient_id}', json=updated_data)

        if response.status_code == 200:
            return redirect(url_for('view_patients'))
        else:
            return jsonify({"error": "Failed to update patient"}), 500

    response = requests.get(f'{PATIENT_DB_SERVICE_URL}/get_patient/{patient_id}')
    if response.status_code == 200:
        patient = response.json().get('patient')
        return render_template('edit_patient.html', patient=patient)
    else:
        return jsonify({"error": "Patient not found"}), 404

@app.route('/delete_patient/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        response = requests.delete(f'{PATIENT_DB_SERVICE_URL}/delete_patient/{patient_id}')
        if response.status_code == 200:
            flash("Patient deleted successfully.")
        else:
            flash("Failed to delete patient.")
    except requests.exceptions.RequestException as e:
        flash(f"Error communicating with Patient Database Service: {e}")

    return redirect(url_for('view_patients'))

@app.route('/add_hospital', methods=['GET', 'POST'])
def add_hospital():
    if request.method == 'POST':
        hospital_data = request.form
        hospital_payload = {
            "name": hospital_data.get("name"),
            "address": hospital_data.get("address")
        }
        try:
            response = requests.post(f'{HOSPITAL_DB_SERVICE_URL}/add_hospital', json=hospital_payload)
            if response.status_code == 201:
                update_hospitals_list()
                return redirect(url_for('view_hospitals'))
            else:
                return f"Failed to add hospital: {response.text}", 500
        except requests.exceptions.RequestException as e:
            return f"Error communicating with Hospital Database Service: {e}", 500
    return render_template('add_hospital.html')

@app.route('/edit_hospital/<int:hospital_id>', methods=['GET', 'POST'])
def edit_hospital(hospital_id):
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')

        updated_data = {"name": name, "address": address}
        response = requests.put(f'{HOSPITAL_DB_SERVICE_URL}/update_hospital/{hospital_id}', json=updated_data)

        if response.status_code == 200:
            return redirect(url_for('view_hospitals'))
        else:
            return jsonify({"error": "Failed to update hospital"}), 500

    response = requests.get(f'{HOSPITAL_DB_SERVICE_URL}/get_hospital/{hospital_id}')
    if response.status_code == 200:
        hospital = response.json().get('hospital')
        return render_template('edit_hospital.html', hospital=hospital)
    else:
        return jsonify({"error": "Hospital not found"}), 404
    
@app.route('/delete_hospital/<int:hospital_id>', methods=['POST'])
def delete_hospital(hospital_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        response = requests.delete(f'{HOSPITAL_DB_SERVICE_URL}/delete_hospital/{hospital_id}')
        if response.status_code == 200:
            update_hospitals_list()
            flash("Hospital deleted successfully.")
        else:
            flash("Failed to delete hospital.")
    except requests.exceptions.RequestException as e:
        flash(f"Error communicating with Hospital Database Service: {e}")

    return redirect(url_for('dashboard'))

@app.route('/confirm_rescue_request/<int:patient_id>', methods=['GET', 'POST'])
def confirm_rescue_request(patient_id):
    if request.method == 'POST':
        response = requests.post(f'http://localhost:5000/prepare_dispatch', json={"patient_id": patient_id})
        if response.status_code == 200:
            flash('Rescue request has been successfully initiated.', 'success')
        else:
            flash('Failed to initiate rescue request.', 'error')
        return redirect(url_for('view_patients'))

    patient_info = next((p for p in patients_list if p['id'] == patient_id), None)
    return render_template('confirm_rescue.html', patient=patient_info)


@app.route('/prepare_dispatch', methods=['POST'])
def prepare_dispatch():
    data = request.json
    patient_id = data.get("patient_id")

    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400

    try:
        patient_response = requests.get(f'{PATIENT_DB_SERVICE_URL}/get_patient/{patient_id}')
        if patient_response.status_code != 200:
            return jsonify({"status": "Patient not found", "error": patient_response.text}), 404

        patient_info = patient_response.json().get("patient")
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error retrieving patient", "error": str(e)}), 500

    best_way = determine_best_way(patient_info)
    closest_hospital = find_closest_hospital(patient_info['address'])

    dispatch_data = {
        "patient_id": patient_info['id'],
        "best_way": best_way,
        "hospital_id": closest_hospital['id']
    }

    try:
        hospital_response = requests.post(f'{HOSPITAL_SERVICE_URL}/prepare_dispatch', json=dispatch_data)
        if hospital_response.status_code == 200:
            return jsonify({"status": "Dispatch prepared", "details": hospital_response.json()}), 200
        else:
            return jsonify({"status": "Failed to prepare dispatch", "error": hospital_response.text}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error communicating with Hospital Service", "error": str(e)}), 500

def determine_best_way(patient_info):
    medical_condition = patient_info.get('medical_condition', "").lower()
    if "blood" in medical_condition:
        return "Immediate Blood Transfusion"
    elif "cardiac" in medical_condition or "heart" in medical_condition or "pressure" in medical_condition:
        return "Cardiac Support Team"
    elif "trauma" in medical_condition or "injury" in medical_condition:
        return "Trauma Rescue"
    elif "stroke" in medical_condition:
        return "Stroke Response Team"
    elif "allergy" in medical_condition or "anaphylaxis" in medical_condition:
        return "Emergency Allergy Support"
    elif "tumor" in medical_condition or "cancer" in medical_condition:
        return "Oncology Emergency Response"
    elif "celiac" in medical_condition or "gluten" in medical_condition:
        return "Dietary Emergency Support"
    elif "infection" in medical_condition or "sepsis" in medical_condition:
        return "Infection Control and Sepsis Response"
    elif "asthma" in medical_condition or "respiratory" in medical_condition:
        return "Respiratory Support Team"
    else:
        return "To be determined on the spot"

def find_closest_hospital(address):
    if not hospitals_list:
        update_hospitals_list()

    if hospitals_list:
        closest_hospital = random.choice(hospitals_list)
        return {"id": closest_hospital['id'], "name": closest_hospital['name']}
    else:
        return {"id": None, "name": "No available hospital"}

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You have been logged out.")
    return redirect(url_for('login'))

app.secret_key = 'secret_key'

if __name__ == "__main__":
    update_patients_list()
    update_hospitals_list()
    app.run(host="0.0.0.0", port=5000)
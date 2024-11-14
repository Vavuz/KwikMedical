import random
from flask import Flask, request, jsonify
import requests
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

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

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Hello from Head Office Microservice!"})

@app.route('/add_patient', methods=['POST'])
def add_patient():
    patient_data = request.json
    try:
        response = requests.post(f'{PATIENT_DB_SERVICE_URL}/add_patient', json=patient_data)
        if response.status_code == 201:
            update_patients_list()
            return jsonify({"status": "Patient added successfully", "data": response.json()}), 201
        else:
            return jsonify({"status": "Failed to add patient", "error": response.text}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error communicating with Patient Database Service", "error": str(e)}), 500

@app.route('/add_hospital', methods=['POST'])
def add_hospital():
    hospital_data = request.json
    try:
        response = requests.post(f'{HOSPITAL_DB_SERVICE_URL}/add_hospital', json=hospital_data)
        if response.status_code == 201:
            update_hospitals_list()
            return jsonify({"status": "Hospital added successfully", "data": response.json()}), 201
        else:
            return jsonify({"status": "Failed to add hospital", "error": response.text}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error communicating with Hospital Database Service", "error": str(e)}), 500

@app.route('/get_patient', methods=['POST'])
def get_patient():
    query_params = request.json
    try:
        response = requests.post(f'{PATIENT_DB_SERVICE_URL}/get_patient', json=query_params)
        if response.status_code == 200:
            return jsonify({"status": "Patient found", "patient": response.json().get("patient")}), 200
        else:
            return jsonify({"status": "Patient not found", "error": response.text}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error communicating with Patient Database Service", "error": str(e)}), 500

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

@app.route('/delete_patient/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        response = requests.delete(f'{PATIENT_DB_SERVICE_URL}/delete_patient/{patient_id}')
        if response.status_code == 200:
            update_patients_list()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error communicating with Patient Database Service", "error": str(e)}), 500

@app.route('/delete_hospital/<int:hospital_id>', methods=['DELETE'])
def delete_hospital(hospital_id):
    try:
        response = requests.delete(f'{HOSPITAL_DB_SERVICE_URL}/delete_hospital/{hospital_id}')
        if response.status_code == 200:
            update_hospitals_list()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error communicating with Hospital Database Service", "error": str(e)}), 500

@app.route('/trigger_update_patients_list', methods=['POST'])
def trigger_update_patients_list():
    update_patients_list()
    return jsonify({"status": "Patients list updated"}), 200


if __name__ == "__main__":
    update_patients_list()
    app.run(host="0.0.0.0", port=5000)
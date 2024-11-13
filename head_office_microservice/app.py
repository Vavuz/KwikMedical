from flask import Flask, request, jsonify
import requests
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

PATIENT_DB_SERVICE_URL = 'http://patient_database_microservice:5000'
HOSPITAL_SERVICE_URL = 'http://hospital_database_microservice:5000'

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Hello from Head Office Microservice!"})

@app.route('/add_patient', methods=['POST'])
def add_patient():
    patient_data = request.json
    try:
        response = requests.post(f'{PATIENT_DB_SERVICE_URL}/add_patient', json=patient_data)
        if response.status_code == 201:
            return jsonify({"status": "Patient added successfully", "data": response.json()}), 201
        else:
            return jsonify({"status": "Failed to add patient", "error": response.text}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error communicating with Patient Database Service", "error": str(e)}), 500

@app.route('/add_hospital', methods=['POST'])
def add_hospital():
    hospital_data = request.json
    try:
        response = requests.post(f'{HOSPITAL_SERVICE_URL}/add_hospital', json=hospital_data)
        if response.status_code == 201:
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
            patient_info = response.json().get("patient")
            if 'address' not in patient_info:
                print("Error: 'address' field is missing in patient_info")
                return jsonify({"error": "Patient data is incomplete", "details": "Missing address"}), 500
            
            best_way = determine_best_way(patient_info)
            closest_hospital = find_closest_hospital(patient_info['address'])
            rescue_request = {
                "patient_id": patient_info['id'],
                "patient_details": patient_info,
                "best_way": best_way,
                "hospital_id": closest_hospital['id']
            }
            
            hospital_response = requests.post(f'{HOSPITAL_SERVICE_URL}/dispatch_ambulance', json=rescue_request)
            if hospital_response.status_code == 200:
                return jsonify({"status": "Ambulance dispatched", "details": hospital_response.json()}), 200
            else:
                return jsonify({"status": "Failed to dispatch ambulance", "error": hospital_response.text}), 500
        else:
            return jsonify({"status": "Patient not found", "error": response.text}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error communicating with Services", "error": str(e)}), 500

def determine_best_way(patient_info):
    return "Standard Rescue"

def find_closest_hospital(address):
    return {"id": 1, "name": "Regional Hospital A"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
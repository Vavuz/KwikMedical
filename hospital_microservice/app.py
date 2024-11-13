from flask import Flask, request, jsonify
import requests
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

AMBULANCE_MOBILE_SERVICE_URL = 'http://ambulance_mobile_microservice:5000'
PATIENT_DATABASE_SERVICE_URL = 'http://patient_database_microservice:5000'

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Hello from Hospital Microservice!"})

@app.route('/dispatch_ambulance', methods=['POST'])
def dispatch_ambulance():
    data = request.json
    patient_id = data.get('patient_id')
    hospital_id = data.get('hospital_id')
    medical_record = get_patient_medical_record(patient_id)
    if not medical_record:
        return jsonify({"status": "Failed to retrieve medical record"}), 404
    try:
        response = requests.post(f'{AMBULANCE_MOBILE_SERVICE_URL}/receive_medical_record', json=medical_record)
        if response.status_code == 200:
            return jsonify({"status": "Ambulance dispatched and medical record sent"}), 200
        else:
            return jsonify({"status": "Failed to send medical record", "error": response.text}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error communicating with Ambulance Mobile Service", "error": str(e)}), 500

@app.route('/receive_call_out_details', methods=['POST'])
def receive_call_out_details():
    data = request.json
    patient_id = data.get('patient_id')
    call_out_details = data.get('call_out_details')
    update_patient_record(patient_id, call_out_details)
    return jsonify({"status": "Call-out details updated"}), 200

def get_patient_medical_record(patient_id):
    try:
        response = requests.get(f'{PATIENT_DATABASE_SERVICE_URL}/get_patient/{patient_id}')
        if response.status_code == 200:
            return response.json().get('patient')
        else:
            return None
    except requests.exceptions.RequestException:
        return None

def update_patient_record(patient_id, call_out_details):
    update_data = {
        "call_out_details": call_out_details
    }
    try:
        response = requests.put(f'{PATIENT_DATABASE_SERVICE_URL}/update_patient/{patient_id}', json=update_data)
        if response.status_code != 200:
            print(f"Failed to update patient record: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Patient Database Service: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
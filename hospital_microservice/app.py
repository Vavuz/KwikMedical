from flask import Flask, request, jsonify
import requests
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

AMBULANCE_MOBILE_SERVICE_URL = 'http://ambulance_mobile_microservice:5000'
PATIENT_DATABASE_SERVICE_URL = 'http://patient_database_microservice:5000'
HEAD_OFFICE_SERVICE_URL = 'http://head_office_microservice:5000'

ready_dispatch_requests = {}
dispatched_requests = {}
call_out_updates = {}

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Hello from Hospital Microservice!"})

@app.route('/prepare_dispatch', methods=['POST'])
def prepare_dispatch():
    data = request.json
    patient_id = data.get('patient_id')
    best_way = data.get('best_way')
    hospital_id = data.get('hospital_id')

    if not (patient_id and best_way and hospital_id):
        return jsonify({"error": "Missing required dispatch information"}), 400

    ready_dispatch_requests[patient_id] = {
        "patient_id": patient_id,
        "best_way": best_way,
        "hospital_id": hospital_id,
    }
    return jsonify({"status": "Dispatch information saved and ready"}), 200

@app.route('/dispatch_ambulance/<int:patient_id>', methods=['POST'])
def dispatch_ambulance(patient_id):
    dispatch_data = ready_dispatch_requests.pop(patient_id, None)
    if not dispatch_data:
        return jsonify({"status": "No ready dispatch information found for this patient"}), 404

    medical_record = get_patient_medical_record(patient_id)
    if not medical_record:
        return jsonify({"status": "Failed to retrieve medical record"}), 404

    try:
        response = requests.post(f'{AMBULANCE_MOBILE_SERVICE_URL}/receive_medical_record', json=medical_record)
        if response.status_code == 200:
            dispatched_requests[patient_id] = dispatch_data
            return jsonify({"status": "Ambulance dispatched and medical record sent"}), 200
        else:
            ready_dispatch_requests[patient_id] = dispatch_data
            return jsonify({"status": "Failed to send medical record", "error": response.text}), 500
    except requests.exceptions.RequestException as e:
        ready_dispatch_requests[patient_id] = dispatch_data
        return jsonify({"status": "Error communicating with Ambulance Mobile Service", "error": str(e)}), 500

@app.route('/receive_call_out_details', methods=['POST'])
def receive_call_out_details():
    data = request.json
    patient_id = data.get('patient_id')
    call_out_details = data.get('call_out_details')
    
    if patient_id and call_out_details:
        call_out_updates[patient_id] = call_out_details
        update_patient_record(patient_id, call_out_details)
        return jsonify({"status": "Call-out details updated"}), 200
    else:
        return jsonify({"error": "Missing patient ID or call-out details"}), 400

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
        else:
            try:
                requests.post(f'{HEAD_OFFICE_SERVICE_URL}/trigger_update_patients_list')
            except requests.exceptions.RequestException as e:
                print(f"Error notifying Head Office to update patients list: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Patient Database Service: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
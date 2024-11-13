from flask import Flask, request, jsonify
import requests
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Hello from Ambulance Mobile Microservice!"})

@app.route('/receive_medical_record', methods=['POST'])
def receive_medical_record():
    data = request.json
    return jsonify({"status": "Medical record received", "data": data}), 200

@app.route('/send_call_out_details', methods=['POST'])
def send_call_out_details():
    data = request.json
    hospital_service_url = 'http://hospital_microservice:5000/update_call_out'
    try:
        response = requests.post(hospital_service_url, json=data)
        if response.status_code == 200:
            return jsonify({"status": "Call-out details sent successfully"}), 200
        else:
            return jsonify({"status": "Failed to send call-out details"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error communicating with Hospital Service", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nhs_number = db.Column(db.String(50), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    medical_condition = db.Column(db.String(200), nullable=False)
    call_out_details = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "nhs_number": self.nhs_number,
            "address": self.address,
            "medical_condition": self.medical_condition,
            "call_out_details": self.call_out_details
        }

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Hello from Patient Database Microservice!"})

@app.route('/add_patient', methods=['POST'])
def add_patient():
    data = request.json
    new_patient = Patient(
        name=data['name'],
        nhs_number=data['nhs_number'],
        address=data['address'],
        medical_condition=data['medical_condition']
    )
    db.session.add(new_patient)
    db.session.commit()
    return jsonify({"status": "Patient added", "patient": new_patient.to_dict()}), 201

@app.route('/get_patient', methods=['POST'])
def get_patient():
    query_params = request.json
    patient = Patient.query.filter_by(**query_params).first()
    if patient:
        return jsonify({"patient": patient.to_dict()}), 200
    else:
        return jsonify({"error": "Patient not found"}), 404

@app.route('/get_patient/<int:patient_id>', methods=['GET'])
def get_patient_with_id(patient_id):
    patient = Patient.query.get(patient_id)
    if patient:
        return jsonify({"patient": patient.to_dict()}), 200
    else:
        return jsonify({"error": "Patient not found"}), 404

@app.route('/get_patients', methods=['GET'])
def get_patients():
    patients = Patient.query.all()
    return jsonify({"patients": [patient.to_dict() for patient in patients]}), 200

@app.route('/update_patient/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.json
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    if 'call_out_details' in data:
        patient.call_out_details = data['call_out_details']

    db.session.commit()
    return jsonify({"status": "Patient updated", "patient": patient.to_dict()}), 200

@app.route('/delete_patient/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    db.session.delete(patient)
    db.session.commit()
    return jsonify({"status": "Patient deleted", "patient_id": patient_id}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
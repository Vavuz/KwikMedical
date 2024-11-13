from sqlalchemy.sql import text
from sqlite3 import OperationalError
import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

def connect_to_database_with_retries():
    """Attempts to connect to the database with retries."""
    attempts = 5
    for attempt in range(attempts):
        try:
            db.session.execute(text("SELECT 1"))
            print("Connected to the database successfully!")
            return True
        except OperationalError:
            print(f"Attempt {attempt + 1} - Database connection failed. Retrying in 5 seconds...")
            time.sleep(5)
    print("Failed to connect to the database after multiple attempts.")
    return False

with app.app_context():
    if connect_to_database_with_retries():
        db.create_all()

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "address": self.address}

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Hello from Hospital Database Microservice!"})

@app.route('/add_hospital', methods=['POST'])
def add_hospital():
    data = request.json
    new_hospital = Hospital(name=data['name'], address=data['address'])
    db.session.add(new_hospital)
    db.session.commit()
    return jsonify({"status": "Hospital added", "hospital": new_hospital.to_dict()}), 201

@app.route('/get_hospitals', methods=['GET'])
def get_hospitals():
    hospitals = Hospital.query.all()
    return jsonify({"hospitals": [hospital.to_dict() for hospital in hospitals]}), 200

@app.route('/get_hospital/<int:hospital_id>', methods=['GET'])
def get_hospital(hospital_id):  
    hospital = Hospital.query.get(hospital_id)
    if hospital:
        return jsonify({"hospital": hospital.to_dict()}), 200
    else:
        return jsonify({"error": "Hospital not found"}), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
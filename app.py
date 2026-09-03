from flask import Flask, request, jsonify, render_template, redirect, url_for, session, make_response, flash
from models import db, Patient, User
import pandas as pd
import joblib
import os
import webbrowser
import pdfkit
from flask_migrate import Migrate

# NEW imports for mail:
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

# ==============================
# Flask Configuration
# ==============================
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ckd_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ==============================
# Gmail SMTP Configuration
# ==============================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "YOUR_GMAIL@gmail.com"
app.config['MAIL_PASSWORD'] = "YOUR_APP_PASSWORD"

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

db.init_app(app)
migrate = Migrate(app, db)

# ==============================
# Load Model
# ==============================
MODEL_PATH = "model.pkl"
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("❌ model.pkl not found. Run train_model.py first.")
model = joblib.load(MODEL_PATH)

# ==============================
# SIGN UP
# ==============================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email already registered")
            return redirect(url_for("signup"))

        user = User(email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Account created! Please sign in.")
        return redirect(url_for("signin"))

    return render_template("signup.html")

# ==============================
# SIGN IN
# ==============================
@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user"] = user.email
            return redirect(url_for("home"))

        flash("Invalid email or password")

    return render_template("signin.html")

# ==============================
# FORGOT PASSWORD (temporary)
# ==============================
@app.route("/forgot-password")
def forgot_password():
    email = request.args.get("email")

    if not email:
        flash("Enter your email first!")
        return redirect(url_for("signin"))

    flash(f"Password reset link sent to {email}")
    return redirect(url_for("signin"))

# ==============================
# LOGOUT
# ==============================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("signin"))

# ==============================
# Require Login
# ==============================
@app.before_request
def require_login():
    allowed_routes = ['signin', 'signup', 'forgot_password', 'static']
    if request.endpoint in allowed_routes or request.endpoint is None:
        return
    if 'user' not in session:
        return redirect(url_for('signin'))

# ==============================
# Page Routes
# ==============================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict-page')
def predict_page():
    return render_template('predict.html')

@app.route('/data')
def data_page():
    return render_template('patient_data.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# ==============================
# CKD Prediction
# ==============================
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        print(f"\n📥 DATA FROM WEBSITE: {data}", flush=True)

        def to_float(value):
            if value in ["", None, "NaN", "null"]:
                return None
            try:
                return float(value)
            except ValueError:
                if str(value).lower() in ['yes', 'true']: return 1.0
                if str(value).lower() in ['no', 'false']: return 0.0
                return None

        # EXACT feature list matching train_model.py
        features_list = [
            'Age (yrs)', 'Blood Pressure (mm/Hg)', 'Specific Gravity',
            'Albumin', 'Sugar', 'Blood Glucose Random (mgs/dL)',
            'Blood Urea (mgs/dL)', 'Serum Creatinine (mgs/dL)',
            'Hemoglobin (gms)', 'Hypertension: yes',
            'Diabetes Mellitus: yes', 'Anemia: yes'
        ]

        # Look for both long names (model) and short names (HTML)
        input_data = {
            'Age (yrs)': to_float(data.get('Age (yrs)', data.get('age'))),
            'Blood Pressure (mm/Hg)': to_float(data.get('Blood Pressure (mm/Hg)', data.get('bp'))),
            'Specific Gravity': to_float(data.get('Specific Gravity', data.get('sg'))),
            'Albumin': to_float(data.get('Albumin', data.get('alb'))),
            'Sugar': to_float(data.get('Sugar', data.get('sugar'))),
            'Blood Glucose Random (mgs/dL)': to_float(data.get('Blood Glucose Random (mgs/dL)', data.get('glucose'))),
            'Blood Urea (mgs/dL)': to_float(data.get('Blood Urea (mgs/dL)', data.get('urea'))),
            'Serum Creatinine (mgs/dL)': to_float(data.get('Serum Creatinine (mgs/dL)', data.get('creatinine'))),
            'Hemoglobin (gms)': to_float(data.get('Hemoglobin (gms)', data.get('hb'))),
            'Hypertension: yes': int(to_float(data.get('Hypertension: yes', data.get('ht', 0))) or 0),
            'Diabetes Mellitus: yes': int(to_float(data.get('Diabetes Mellitus: yes', data.get('dm', 0))) or 0),
            'Anemia: yes': int(to_float(data.get('Anemia: yes', data.get('anemia', 0))) or 0)
        }

        normal_reference = {
            'Age (yrs)': 40, 'Blood Pressure (mm/Hg)': 120, 'Specific Gravity': 1.015,
            'Albumin': 0, 'Sugar': 0, 'Blood Glucose Random (mgs/dL)': 110,
            'Blood Urea (mgs/dL)': 15, 'Serum Creatinine (mgs/dL)': 1.0,
            'Hemoglobin (gms)': 14, 'Hypertension: yes': 0,
            'Diabetes Mellitus: yes': 0, 'Anemia: yes': 0
        }

        # Fill any missing values with the normal reference
        for key in input_data:
            if input_data[key] is None:
                input_data[key] = normal_reference[key]

        print(f"🧠 DATA FED TO MODEL: {input_data}", flush=True)

        # Force exact column order
        df = pd.DataFrame([input_data])[features_list]

        prediction = int(model.predict(df)[0])
        print(f"🎯 RAW PREDICTION NUMBER: {prediction}", flush=True)
        
        result = "CKD Detected" if prediction == 1 else "No CKD"

        patient = Patient(
            name=data.get('name', 'Unknown'),
            age=input_data['Age (yrs)'],
            bp=input_data['Blood Pressure (mm/Hg)'],
            sg=input_data['Specific Gravity'],
            alb=input_data['Albumin'],
            sugar=input_data['Sugar'],
            glucose=input_data['Blood Glucose Random (mgs/dL)'],
            urea=input_data['Blood Urea (mgs/dL)'],
            creatinine=input_data['Serum Creatinine (mgs/dL)'],
            hb=input_data['Hemoglobin (gms)'],
            ht=input_data['Hypertension: yes'],
            dm=input_data['Diabetes Mellitus: yes'],
            anemia=input_data['Anemia: yes'],
            result=result
        )

        db.session.add(patient)
        db.session.commit()

        return jsonify({'prediction': result})

    except Exception as e:
        print(f"❌ ERROR: {e}", flush=True)
        return jsonify({'error': str(e)}), 500

# ==============================
# Fetch All Patients
# ==============================
@app.route('/patients', methods=['GET'])
def get_patients():
    patients = Patient.query.all()
    return jsonify([
        {
            'id': p.id, 'name': p.name, 'age': p.age, 'bp': p.bp,
            'sg': p.sg, 'alb': p.alb, 'sugar': p.sugar, 'glucose': p.glucose,
            'urea': p.urea, 'creatinine': p.creatinine, 'hb': p.hb, 'ht': p.ht,
            'dm': p.dm, 'anemia': p.anemia, 'result': p.result
        }
        for p in patients
    ])

# ==============================
# PDF Download
# ==============================
@app.route('/download-pdf/<int:patient_id>')
def download_pdf(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    html = render_template("patient_pdf.html", patient=patient)

    try:
        # Check both possible Windows installation paths
        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        if not os.path.exists(path_wkhtmltopdf):
            path_wkhtmltopdf = r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
            
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        
        # FIX: Allow wkhtmltopdf to load local files (like CSS) so it doesn't crash
        options = {
            'enable-local-file-access': None
        }
        
        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Patient_{patient.name}_{patient_id}.pdf'
        return response
    except Exception as e:
        # Print the REAL error to the terminal so we can see it if it fails again
        print(f"PDF GENERATION ERROR: {str(e)}")
        return jsonify({'error': f"PDF generation failed: {e}"}), 500

# ==============================
# Delete All Patients
# ==============================
@app.route('/delete-all', methods=['DELETE'])
def delete_all():
    Patient.query.delete()
    db.session.commit()
    return jsonify({'message': 'All patient records deleted.'})

# ==============================
# Run Flask
# ==============================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    webbrowser.open("http://127.0.0.1:5000/signin")
    app.run(debug=True)
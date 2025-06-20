import pickle
import datetime
import uuid
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)

# Load the trained model
with open("health_model.pkl", "rb") as file:
    model = pickle.load(file)
app.secret_key = "prahallad2005"

# Temporary storage for reports (in-memory cache)
report_cache = {}

# Define symptoms list
SYMPTOMS = [
    'itching', 'skin_rash', 'nodal_skin_eruptions', 'continuous_sneezing',
    'shivering', 'chills', 'joint_pain', 'stomach_pain', 'acidity',
    'ulcers_on_tongue', 'muscle_wasting', 'vomiting', 'burning_micturition',
    'spotting_urination', 'fatigue', 'weight_gain', 'anxiety', 'cold_hands_and_feets',
    'mood_swings', 'weight_loss', 'restlessness', 'lethargy', 'patches_in_throat',
    'irregular_sugar_level', 'cough', 'high_fever', 'sunken_eyes', 'breathlessness',
    'sweating', 'dehydration', 'indigestion', 'headache', 'yellowish_skin',
    'dark_urine', 'nausea', 'loss_of_appetite', 'pain_behind_the_eyes',
    'back_pain', 'constipation', 'abdominal_pain', 'diarrhoea',
    'mild_fever', 'yellow_urine', 'yellowing_of_eyes', 'acute_liver_failure',
    'fluid_overload', 'swelling_of_stomach', 'swelled_lymph_nodes', 'malaise',
    'blurred_and_distorted_vision', 'phlegm', 'throat_irritation',
    'redness_of_eyes', 'sinus_pressure', 'runny_nose', 'congestion',
    'chest_pain', 'weakness_in_limbs', 'fast_heart_rate', 'pain_during_bowel_movements',
    'pain_in_anal_region', 'bloody_stool', 'irritation_in_anus', 'neck_pain',
    'dizziness', 'cramps', 'bruising', 'obesity', 'swollen_legs',
    'swollen_blood_vessels', 'puffy_face_and_eyes', 'enlarged_thyroid',
    'brittle_nails', 'swollen_extremeties', 'excessive_hunger', 'extra_marital_contacts',
    'drying_and_tingling_lips', 'slurred_speech', 'knee_pain', 'hip_joint_pain',
    'muscle_weakness', 'stiff_neck', 'swelling_joints', 'movement_stiffness',
    'spinning_movements', 'loss_of_balance', 'unsteadiness', 'weakness_of_one_body_side',
    'loss_of_smell', 'bladder_discomfort', 'foul_smell_of urine',
    'continuous_feel_of_urine', 'passage_of_gases', 'internal_itching',
    'toxic_look_(typhos)', 'depression', 'irritability', 'muscle_pain',
    'altered_sensorium', 'red_spots_over_body', 'belly_pain', 'abnormal_menstruation',
    'dischromic _patches', 'watering_from_eyes', 'increased_appetite',
    'polyuria', 'family_history', 'mucoid_sputum', 'rusty_sputum',
    'lack_of_concentration', 'visual_disturbances', 'receiving_blood_transfusion',
    'receiving_unsterile_injections', 'coma', 'stomach_bleeding', 'distention_of_abdomen',
    'history_of_alcohol_consumption', 'fluid_overload.1', 'blood_in_sputum',
    'prominent_veins_on_calf', 'palpitations', 'painful_walking',
    'pus_filled_pimples', 'blackheads', 'scurring', 'skin_peeling',
    'silver_like_dusting', 'small_dents_in_nails', 'inflammatory_nails',
    'blister', 'red_sore_around_nose', 'yellow_crust_ooze'
]

# Disease information dictionary
disease_info = {
    'Fungal infection': {
        "description": "A fungal infection occurs when an invading fungus takes over an area of the body and is too much for the immune system to handle.",
        "recommendation": "Consult a dermatologist for antifungal medications. Keep the affected area clean and dry."
    },
    'Allergy': {
        "description": "Allergies occur when your immune system reacts to a foreign substance that doesn't cause a reaction in most people.",
        "recommendation": "Avoid known allergens. Use antihistamines or consult an allergist for immunotherapy."
    },
    'GERD': {
        "description": "Gastroesophageal reflux disease (GERD) is a chronic digestive disorder that occurs when stomach acid frequently flows back into the esophagus.",
        "recommendation": "Avoid trigger foods, eat smaller meals, and elevate the head of your bed. Consult a gastroenterologist."
    },
    'Chronic cholestasis': {
        "description": "A condition where bile cannot flow from the liver to the duodenum, leading to bile accumulation in the liver.",
        "recommendation": "Consult a hepatologist for proper diagnosis and management. Treatment may include medications or surgery."
    },
    'Drug Reaction': {
        "description": "An adverse reaction to a medication that can range from mild to life-threatening.",
        "recommendation": "Discontinue the medication if possible and consult your healthcare provider immediately."
    },
    'Peptic ulcer disease': {
        "description": "Sores that develop on the lining of the stomach, upper small intestine or esophagus.",
        "recommendation": "Avoid NSAIDs, alcohol, and smoking. Take prescribed medications and follow a balanced diet."
    },
    'AIDS': {
        "description": "Acquired Immunodeficiency Syndrome is a chronic, potentially life-threatening condition caused by the human immunodeficiency virus (HIV).",
        "recommendation": "Seek immediate medical care for antiretroviral therapy and regular monitoring."
    },
    'Diabetes': {
        "description": "A chronic disease that occurs when the pancreas does not produce enough insulin or when the body cannot effectively use the insulin it produces.",
        "recommendation": "Monitor blood sugar regularly, follow a diabetic diet, exercise, and take medications as prescribed."
    },
    'Gastroenteritis': {
        "description": "Inflammation of the stomach and intestines, typically resulting from bacterial toxins or viral infection.",
        "recommendation": "Stay hydrated, follow the BRAT diet (bananas, rice, applesauce, toast), and rest."
    },
    'Bronchial Asthma': {
        "description": "A condition in which your airways narrow and swell and may produce extra mucus, making breathing difficult.",
        "recommendation": "Use prescribed inhalers, avoid triggers, and have an asthma action plan."
    },
    'Hypertension': {
        "description": "High blood pressure is a common condition where the long-term force of blood against artery walls is high enough to cause health problems.",
        "recommendation": "Monitor blood pressure regularly, reduce sodium intake, exercise, and take prescribed medications."
    },
    'Migraine': {
        "description": "A neurological condition characterized by intense, debilitating headaches often accompanied by nausea, vomiting, and sensitivity to light and sound.",
        "recommendation": "Identify and avoid triggers, rest in a quiet, dark room, and take prescribed medications."
    },
    'Cervical spondylosis': {
        "description": "A general term for age-related wear and tear affecting the spinal disks in your neck.",
        "recommendation": "Practice good posture, do neck exercises, use a supportive pillow, and consider physical therapy."
    },
    'Paralysis (brain hemorrhage)': {
        "description": "Loss of muscle function in part of your body due to bleeding in the brain.",
        "recommendation": "Seek emergency medical care immediately. Rehabilitation therapy is crucial for recovery."
    },
    'Jaundice': {
        "description": "A condition in which the skin, whites of the eyes and mucous membranes turn yellow due to high bilirubin levels.",
        "recommendation": "Consult a healthcare provider to determine the underlying cause and appropriate treatment."
    },
    'Malaria': {
        "description": "A life-threatening mosquito-borne blood disease caused by a Plasmodium parasite.",
        "recommendation": "Seek immediate medical attention. Prevent mosquito bites and take antimalarial drugs if traveling to endemic areas."
    },
    'Chicken pox': {
        "description": "A highly contagious viral infection causing an itchy, blister-like rash on the skin.",
        "recommendation": "Get plenty of rest, use calamine lotion for itching, and stay home until all blisters have crusted over."
    },
    'Dengue': {
        "description": "A mosquito-borne viral infection causing flu-like illness that can develop into severe dengue.",
        "recommendation": "Rest, stay hydrated, and seek medical care immediately if symptoms worsen."
    },
    'Typhoid': {
        "description": "A bacterial infection caused by Salmonella typhi that spreads through contaminated food and water.",
        "recommendation": "Seek medical care for antibiotics. Practice good hygiene and food safety."
    },
    'Hepatitis A': {
        "description": "A highly contagious liver infection caused by the hepatitis A virus.",
        "recommendation": "Get vaccinated, rest, stay hydrated, and avoid alcohol. Most people recover without treatment."
    },
    'Hepatitis B': {
        "description": "A serious liver infection caused by the hepatitis B virus that can become chronic.",
        "recommendation": "Get vaccinated, avoid alcohol, and consult a healthcare provider for antiviral medications if needed."
    },
    'Hepatitis C': {
        "description": "A viral infection that causes liver inflammation, sometimes leading to serious liver damage.",
        "recommendation": "Consult a healthcare provider for antiviral medications. Avoid alcohol and get vaccinated against hepatitis A and B."
    },
    'Hepatitis D': {
        "description": "A serious liver disease caused by infection with the hepatitis D virus that only occurs in people infected with hepatitis B.",
        "recommendation": "Consult a hepatologist for specialized care. Prevention involves hepatitis B vaccination."
    },
    'Hepatitis E': {
        "description": "A liver disease caused by the hepatitis E virus that usually results in an acute infection.",
        "recommendation": "Rest, stay hydrated, and avoid alcohol. Most people recover without treatment."
    },
    'Alcoholic hepatitis': {
        "description": "Liver inflammation caused by excessive alcohol consumption over time.",
        "recommendation": "Stop drinking alcohol immediately. Seek medical care for supportive treatment."
    },
    'Tuberculosis': {
        "description": "A potentially serious infectious bacterial disease that mainly affects the lungs.",
        "recommendation": "Complete the full course of antibiotics as prescribed. Cover your mouth when coughing."
    },
    'Common Cold': {
        "description": "A viral infection of your upper respiratory tract — your nose and throat.",
        "recommendation": "Rest, stay hydrated, and use over-the-counter cold remedies to relieve symptoms."
    },
    'Pneumonia': {
        "description": "An infection that inflames the air sacs in one or both lungs, which may fill with fluid.",
        "recommendation": "Seek medical care for antibiotics if bacterial. Rest and stay hydrated."
    },
    'Dimorphic hemorrhoids(piles)': {
        "description": "Swollen and inflamed veins in the rectum and anus that cause discomfort and bleeding.",
        "recommendation": "Increase fiber intake, drink plenty of water, and use over-the-counter creams for relief."
    },
    'Heart attack': {
        "description": "A blockage of blood flow to the heart muscle, often due to a blood clot.",
        "recommendation": "Seek emergency medical care immediately. Call your local emergency number."
    },
    'Varicose veins': {
        "description": "Enlarged, twisted veins that most commonly occur in the legs.",
        "recommendation": "Exercise regularly, elevate your legs, wear compression stockings, and avoid long periods of standing."
    },
    'Hypothyroidism': {
        "description": "A condition where the thyroid gland doesn't produce enough thyroid hormone.",
        "recommendation": "Take prescribed thyroid hormone replacement medication regularly and have regular TSH tests."
    },
    'Hyperthyroidism': {
        "description": "A condition where the thyroid gland produces too much thyroid hormone.",
        "recommendation": "Consult an endocrinologist for appropriate treatment which may include medication, radioactive iodine, or surgery."
    },
    'Hypoglycemia': {
        "description": "A condition characterized by abnormally low blood sugar levels.",
        "recommendation": "Eat small, frequent meals, carry fast-acting sugar sources, and monitor blood sugar regularly."
    },
    'Osteoarthritis': {
        "description": "The most common form of arthritis, occurring when the protective cartilage at the ends of bones wears down over time.",
        "recommendation": "Maintain a healthy weight, exercise regularly, and use pain relievers as needed."
    },
    'Arthritis': {
        "description": "Inflammation of one or more joints, causing pain and stiffness.",
        "recommendation": "Exercise regularly, maintain a healthy weight, and use prescribed medications to manage symptoms."
    },
    '(Vertigo) Paroxysmal Positional Vertigo': {
        "description": "A sudden sensation of spinning, usually triggered by specific changes in head position.",
        "recommendation": "Perform repositioning maneuvers like the Epley maneuver under professional guidance."
    },
    'Acne': {
        "description": "A skin condition that occurs when hair follicles become plugged with oil and dead skin cells.",
        "recommendation": "Keep skin clean, avoid squeezing pimples, and use over-the-counter or prescription treatments."
    },
    'Urinary tract infection': {
        "description": "An infection in any part of the urinary system, most commonly the bladder and urethra.",
        "recommendation": "Drink plenty of water, urinate frequently, and take prescribed antibiotics."
    },
    'Psoriasis': {
        "description": "A chronic autoimmune condition that causes rapid buildup of skin cells, leading to scaling on the skin's surface.",
        "recommendation": "Moisturize regularly, avoid triggers, and use prescribed topical treatments or medications."
    },
    'Impetigo': {
        "description": "A highly contagious skin infection that mainly affects infants and children.",
        "recommendation": "Keep skin clean, avoid scratching, and use prescribed antibiotic ointment or oral antibiotics."
    }
}

@app.route('/')
def index():
    """Render the main index page."""
    return render_template('index.html', symptoms=SYMPTOMS)

@app.route('/predict', methods=['POST'])
def predict():
    """Handle disease prediction requests."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    selected_symptoms = data.get('symptoms', [])
    user_details = data.get('userDetails', {})
    
    name = user_details.get('name', '')
    age = user_details.get('age', '')
    blood_group = user_details.get('bloodGroup', '')

    # Validate inputs
    if not selected_symptoms:
        return jsonify({"error": "No symptoms selected"}), 400
    if not name or not age:
        return jsonify({"error": "Missing required user details"}), 400

    # Convert to model input format
    input_data = [1 if symptom in selected_symptoms else 0 for symptom in SYMPTOMS]

    # Predict disease using trained model
    try:
        prediction = model.predict([input_data])[0]
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

    # Fetch extra info about disease
    disease_data = disease_info.get(prediction, {})
    description = disease_data.get("description", "No description available.")
    recommendation = disease_data.get("recommendation", "Please consult a healthcare provider.")

    # Generate unique report ID
    report_id = str(uuid.uuid4())
    
    # Store result in temporary cache
    report_cache[report_id] = {
        'prediction': prediction,
        'description': description,
        'recommendation': recommendation,
        'name': name,
        'age': age,
        'blood_group': blood_group,
        'symptoms': selected_symptoms
    }

    # Return JSON response with report ID
    return jsonify({
        'prediction': prediction,
        'description': description,
        'recommendation': recommendation,
        'report_id': report_id
    })

@app.route('/download-report/<report_id>')
def download_report(report_id):
    """Generate and serve PDF health report."""
    result = report_cache.get(report_id)
    if not result:
        return jsonify({"error": "Report not found or expired. Please generate a new prediction."}), 404

    try:
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom style for italic text
        italic_style = ParagraphStyle(
            'Italic',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique'
        )
        
        elements = []

        # Title Section
        elements.append(Paragraph("Health Prediction Report", styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Patient Information Section
        elements.append(Paragraph("Patient Information", styles['Heading2']))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>Name:</b> {result.get('name', 'Not provided')}", styles['Normal']))
        elements.append(Paragraph(f"<b>Age:</b> {result.get('age', 'Not provided')}", styles['Normal']))
        elements.append(Paragraph(f"<b>Blood Group:</b> {result.get('blood_group', 'Not provided')}", styles['Normal']))
        elements.append(Paragraph(f"<b>Report Date:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 16))

        # Prediction Results
        elements.append(Paragraph("Disease Prediction Result", styles['Heading2']))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>Predicted Disease:</b> {result['prediction']}", styles['Normal']))
        elements.append(Paragraph(f"<b>Description:</b> {result['description']}", styles['Normal']))
        elements.append(Paragraph(f"<b>Recommendation:</b> {result['recommendation']}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Symptoms Section
        elements.append(Paragraph("Reported Symptoms", styles['Heading2']))
        elements.append(Spacer(1, 8))
        symptom_list = [f"• {symptom.replace('_', ' ').title()}" for symptom in result['symptoms']]
        elements.append(Paragraph("<br/>".join(symptom_list), styles['Normal']))
        elements.append(Spacer(1, 20))

        # General Health Advice
        elements.append(Paragraph("General Health Advice", styles['Heading2']))
        elements.append(Spacer(1, 8))
        advice = [
            "• Always consult with a healthcare professional for medical advice",
            "• Maintain a balanced diet and stay hydrated",
            "• Get regular exercise and adequate sleep",
            "• Practice good hygiene and preventive care",
            "• Follow prescribed treatments and medications",
            "• Monitor symptoms and seek help if they worsen"
        ]
        for item in advice:
            elements.append(Paragraph(item, styles['Normal']))
        
        # Disclaimer
        elements.append(Spacer(1, 20))
        disclaimer = (
            "This report is generated by an AI system and should not replace professional medical advice. "
            "Always consult with a qualified healthcare provider for diagnosis and treatment."
        )
        elements.append(Paragraph(disclaimer, italic_style))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        # Create filename
        patient_name = result.get('name', 'Health_Report').replace(" ", "_")
        filename = f"{patient_name}_Health_Report.pdf"

        # Return PDF
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
import streamlit as st 
import os
import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
import random
import time
import webbrowser

# --- Page Config ---
st.set_page_config(page_title="AI Health Assistant", page_icon="🩺", layout="centered")

# --- Custom CSS Styling ---
st.markdown("""
    <style>
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 1050px !important;  /* Optional: increase max width */
            margin-left: auto;
            margin-right: auto;
        }
        
        .stApp {
            background: linear-gradient(135deg, #156b94 0%, #156b94 100%);
            font-size: 20px !important;
        }
        body {
            background-color: #87cefa;
            color: #003366;
        }
        .main {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        h1{
            color: #123350 !important;
            text-align: center;
            font-size: 50px !important
            }
        h2, h5, h3, h4 {
            color: #123350 !important;
            text-align: center;
            font-size: 36px !important;
        }
        .stButton>button {
            background-color: #3b8bfa;
            color: white;
            border: none;
            padding: 0.7em 1.2em;
            border-radius: 8px;
            transition: 0.3s;
            font-size: 18px !important;
        }
        .stButton>button:hover {
            background-color: #0056b3;
            transform: scale(1.02);
        }
        .stRadio>div>label, .stSlider>div, .st-expanderHeader, .stMarkdown {
            font-size: 20px !important;
            color: #003366 !important;
        }
        .highlight-box {
            background-color: #0056b3;
            color: white !important;
            padding: 1rem;
            border-radius: 8px;
            border-left: 5px solid #3b8bfa;
            margin-bottom: 1rem;
            font-size: 20px;
        }
            
    </style>
""", unsafe_allow_html=True)

# --- Load Vosk model ---
if not os.path.exists("model"):
    st.error("🚨 Vosk model not found. Please unzip it into a folder named 'model'.")
    st.stop()

model = Model("model")
recognizer = KaldiRecognizer(model, 16000)
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        st.warning(status)
    q.put(bytes(indata))

def record_audio(duration=5):
    audio_data = b""
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        start_time = time.time()
        while time.time() - start_time < duration:
            audio_data += q.get()
    return audio_data

# --- Symptom Dictionary ---
symptom_keywords = {
    "headache": ("Headache", "💡 Rest in a quiet room, stay hydrated, and consider pain relievers."),
     "cough": ("Cough", "💡 Drink warm fluids and avoid irritants. Consult if persistent."),
    "fever": ("Fever", "💡 Keep hydrated, monitor temperature, seek help if >39°C or >3 days."),
    "sore throat": ("Sore Throat", "💡 Gargle warm salt water, avoid irritants."),
    "nausea": ("Nausea", "💡 Eat small bland meals, stay hydrated."),
    "vomiting": ("Vomiting", "💡 Sip water or oral rehydration solutions."),
    "diarrhea": ("Diarrhea", "💡 Maintain hydration, avoid dairy, see doctor if severe."),
    "fatigue": ("Fatigue", "💡 Get rest and balanced nutrition."),
    "tired": ("Fatigue", "💡 Get rest and balanced nutrition."),
    "dizzy": ("Dizziness", "💡 Sit or lie down, avoid sudden movements."),
    "dizziness": ("Dizziness", "💡 Sit or lie down, avoid sudden movements."),
    "chest pain": ("Chest Pain", "⚠️ Seek emergency medical attention immediately!"),
    "shortness of breath": ("Shortness of Breath", "⚠️ Seek urgent medical help!"),
    "difficulty breathing": ("Shortness of Breath", "⚠️ Seek urgent medical help!"),
    "runny nose": ("Runny Nose", "💡 Use saline sprays, rest."),
    "congestion": ("Nasal Congestion", "💡 Use steam inhalation or decongestants."),
    "sneezing": ("Sneezing", "💡 Avoid allergens."),
    "muscle pain": ("Muscle Pain", "💡 Rest and warm compresses."),
    "body ache": ("Body Ache", "💡 Rest, hydrate, consider painkillers."),
    "rash": ("Skin Rash", "💡 Avoid scratching, use soothing lotions."),
    "itchy skin": ("Itchy Skin", "💡 Use moisturizers, avoid irritants."),
    "loss of smell": ("Loss of Smell", "💡 Monitor and consult if persistent."),
    "loss of taste": ("Loss of Taste", "💡 Maintain oral hygiene, consult if persistent."),
    "abdominal pain": ("Abdominal Pain", "💡 Monitor severity, seek help if severe."),
    "stomach ache": ("Stomach Ache", "💡 Eat bland foods, avoid heavy meals."),
    "chills": ("Chills", "💡 Keep warm and rest."),
    "blurred vision": ("Blurred Vision", "⚠️ Seek immediate medical attention!"),
    "earache": ("Earache", "💡 Avoid inserting objects, consult if persists."),
    "joint pain": ("Joint Pain", "💡 Rest and apply ice or heat."),
    "swelling": ("Swelling", "💡 Elevate and apply cold compresses."),
    "bleeding": ("Bleeding", "⚠️ Apply pressure, seek emergency care if severe."),
    "palpitations": ("Heart Palpitations", "💡 Avoid stimulants, seek evaluation if frequent.")
}

# --- Title Section ---
st.markdown("<h1>🩺 AI Health Assistant</h1>", unsafe_allow_html=True)
st.markdown("<h5>Check symptoms and simulate vital signs using voice or text.</h5>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
    <div style="background-color: #ced9ff; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);">
        <h2 style="color: #0056b3;">🩺 About Us</h2>
        <p style="font-size: 16px; color: #333;">
            Welcome to <strong>HealthAI Assistant</strong> — your intelligent partner for better health!
        </p>
        <p style="font-size: 16px; color: #333;">
            At HealthAI Assistant, we believe that access to health information should be 
            <strong>fast</strong>, <strong>accurate</strong>, and <strong>stress-free</strong>. 
            Our system combines artificial intelligence, natural language processing, and 
            secure video communication to empower individuals to understand their symptoms, 
            monitor their vitals, and connect with medical professionals in real-time.
        </p>
        <p style="font-size: 16px; color: #333;">
            <strong>🔐 Our Commitment</strong><br>
            We prioritize your <strong>privacy</strong> and <strong>security</strong>. 
            All communications are encrypted, and no personal health data is shared without consent. 
        </p> 
         <p style="font-size: 16px; color: #333;">
            <strong>🌍 Our Vision</strong><br>
            To transform digital healthcare by making intelligent, accessible, and human-centered tools 
            that bring peace of mind and better outcomes — anytime, anywhere.
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- Step 1: Symptom Detection ---
st.subheader("📌 Symptom Checker (Voice or Text)")

col1, col2 = st.columns([1, 2])
with col1:
    if st.button("🎙️ Start Voice Recording"):
        st.info("⏺️ Listening... Speak now (5 seconds)")
        audio_bytes = record_audio(duration=5)
        if recognizer.AcceptWaveform(audio_bytes):
            result = json.loads(recognizer.Result())
            recognized_text = result.get("text", "")
            if recognized_text:
                st.success(f"✅ Recognized: '{recognized_text}'")
            else:
                st.error("❌ Could not clearly recognize speech.")
                recognized_text = ""
        else:
            st.error("❌ Audio processing failed.")
            recognized_text = ""
    else:
        recognized_text = ""

with col2:

    # 1) Inject CSS to style the actual <textarea> widget
    st.markdown("""
    <style>
    .stTextArea label, .stTextInput label {
            font-weight: bold;
            font-size: 20px !important;
            color: #ffffff !important;
        }
        .stTextArea > div > div > textarea,
        .stTextInput > div > div > input {
            background-color: #123350 !important;
            color: #ffffff !important;
            font-size: 18px !important;
            border-radius: 10px !important;
            padding: 10px !important;
            border: none !important;
        }
        .stTextArea > div > div > textarea:focus,
        .stTextInput > div > div > input:focus {
            outline: 2px solid #ffaa44 !important;
        }

    </style>
    """, unsafe_allow_html=True)

    # 2) Now render the text area; our CSS will style it
    typed_symptoms = st.text_area(
        "📝 Or type your symptoms here:", 
        placeholder="e.g. headache, sore throat, fatigue...", 
        height=150
    )


# --- Process Symptoms ---
combined_input = f"{typed_symptoms} {recognized_text}".strip().lower()
detected_symptoms = []

for keyword, (label, suggestion) in symptom_keywords.items():
    if keyword in combined_input and label not in detected_symptoms:
        detected_symptoms.append(label)

if detected_symptoms:
    st.markdown("<div class='highlight-box'>🧾 <strong>Detected symptoms:</strong> " + ", ".join(detected_symptoms) + "</div>", unsafe_allow_html=True)
    for symptom in detected_symptoms:
        _, suggestion = symptom_keywords.get(symptom.lower(), (symptom, "💡 Consult a healthcare professional."))
        st.info(f"{symptom}: {suggestion}")
elif combined_input:
    st.success("✅ No major symptoms detected. You seem fine.")

st.markdown("---")

# --- Step 2: Vital Signs ---
st.subheader("🧪 Vital Sign Collection")

mode = st.radio("📊 Choose Data Mode:", ["User Input", "Random Simulation"], horizontal=True)

if mode == "User Input":
    with st.expander("🧍 Enter Your Vital Signs"):
        temp = st.slider("🌡️ Body Temperature (°C)", 35.0, 42.0, 36.5)
        heart_rate = st.slider("❤️ Heart Rate (bpm)", 40, 180, 75)
        systolic = st.slider("🩸 Systolic BP", 90, 200, 120)
        diastolic = st.slider("🩸 Diastolic BP", 60, 130, 80)
else:
    temp = round(random.uniform(36, 40), 1)
    heart_rate = random.randint(60, 150)
    systolic = random.randint(100, 180)
    diastolic = random.randint(70, 110)

    st.markdown(f"""
        <div class='highlight-box'>
        <div style="background-color: #0056b3;  padding: 10px; border-radius: 10px; font-size: 16px;">
        <strong>Simulated Vitals:</strong><br>
        🌡️ Temperature: <strong>{temp} °C</strong><br>
        ❤️ Heart Rate: <strong>{heart_rate} bpm</strong><br>
        🩸 Blood Pressure: <strong>{systolic}/{diastolic} mmHg</strong>
    </div>
    """, unsafe_allow_html=True)

# --- Analyze Vitals ---
alerts, suggestions = [], []

if temp > 38:
    alerts.append("High Temperature (Fever)")
    suggestions.append("💡 Rest and hydrate. Seek help if fever persists.")
elif temp < 36:
    alerts.append("Low Temperature")
    suggestions.append("💡 Stay warm and monitor for chills.")

if heart_rate > 100:
    alerts.append("High Heart Rate")
    suggestions.append("💡 Rest and breathe deeply.")
elif heart_rate < 60:
    alerts.append("Low Heart Rate")
    suggestions.append("💡 Monitor. Seek advice if accompanied by symptoms.")

if systolic > 140 or diastolic > 90:
    alerts.append("High Blood Pressure")
    suggestions.append("💡 Reduce salt, manage stress.")
elif systolic < 90 or diastolic < 60:
    alerts.append("Low Blood Pressure")
    suggestions.append("💡 Stay hydrated, avoid sudden movements.")

if alerts:
    st.warning("⚠️ Abnormal Vitals Detected:")
    for alert in alerts:
        st.markdown(f"<span style='color:white'>• {alert}</span>", unsafe_allow_html=True)
    st.markdown("#### ✅ Health Suggestions:")
    for tip in suggestions:
        st.info(tip)
else:
    st.success("🎉 All vitals appear normal!")

st.markdown("---")

# --- Step 3: Teleconsultation ---
st.subheader("📞Teleconsultation")

# --- Style the text_input box ---
st.markdown("""
<style>
/* Label styling */
.stTextInput label {
    font-weight: bold;
    color: #ffffff !important;
}
/* Input box styling */
.stTextInput > div > div > input {
    background-color: #123350 !important;
    color: #ffffff !important;
    font-size: 16px !important;
    border-radius: 10px !important;
    padding: 10px !important;
    border: none !important;
}
/* Focus effect */
.stTextInput > div > div > input:focus {
    outline: 2px solid #ffaa44 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Your styled input field ---
room = st.text_input("Enter Room Name for Video Call", value="HealthAIConsultRoom")

jitsi_url = f"https://meet.jit.si/HealthAIConsultRoom"

if st.button("📞 Call Doctor Now"):
    st.success(f"Launching video call room: {room}")
    webbrowser.open(jitsi_url)

import streamlit as st
import pandas as pd
from datetime import datetime
import threading
from queue import Queue
import folium
from streamlit_folium import st_folium
from gtts import gTTS
import os
import speech_recognition as sr
import geocoder  # For auto-detecting location
import ollama

# Initialize Ollama API
ollama.api_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIX8uYFNgw2VK7HpZE/VsykA6gy5fVRElMG9RYckhq9K"
model_name = "llama3"  # Replace with your locally hosted model

# Queue for handling asynchronous requests
response_queue = Queue()

# Function to generate response from Ollama model
def get_response(prompt, queue):
    try:
        disaster_prompt = f"""
        You are a disaster-assistance chatbot. Your role is to provide actionable advice and critical assistance 
        during emergencies. Focus on first aid, locating shelters, and safety instructions. Be concise and 
        prioritize urgent information. 

        User Query: {prompt}
        """
        raw_response = ollama.generate(model=model_name, prompt=disaster_prompt)
        response = raw_response.get("response", "No response received.")
        queue.put(response)
    except Exception as e:
        queue.put(f"Error: {str(e)}")

# Function to save data to Excel
def save_to_excel(data):
    try:
        # Batch writes to Excel
        try:
            existing_data = pd.read_excel("disaster_chatbot_data.xlsx", engine='openpyxl')
            updated_data = pd.concat([existing_data, data], ignore_index=True)
        except FileNotFoundError:
            updated_data = data
        updated_data.to_excel("disaster_chatbot_data.xlsx", index=False, engine='openpyxl')
    except Exception as e:
        st.write(f"Error saving data to Excel: {str(e)}")

# Function to convert text to speech and play it
def text_to_speech(text):
    try:
        tts = gTTS(text)
        tts.save("response.mp3")
        os.system("start response.mp3" if os.name == "nt" else "afplay response.mp3")
    except Exception as e:
        st.write(f"Error with text-to-speech: {str(e)}")

# Function to convert voice input to text
def voice_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening... Please speak clearly.")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I could not understand your speech."
        except sr.RequestError as e:
            return f"Could not request results; {e}"
        except Exception as e:
            return f"Error: {str(e)}"

# Auto-detect user location using geocoder
def get_user_location():
    try:
        location = geocoder.ip("me").latlng
        if location:
            return location
    except Exception as e:
        st.write(f"Error detecting location: {str(e)}")
    # Default to Wayanad if location detection fails
    return [11.6854, 76.1320]

# Streamlit UI Setup with Custom Styling
st.markdown(
    """
    <style>
    body {
        background-color: #fff4e6;
        color: black;
        font-family: Arial, sans-serif;
    }
    .stButton > button {
        background-color: #d9534f;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px;
        font-size: 16px;
    }
    .stButton > button:hover {
        background-color: #c9302c;
    }
    .stRadio > div {
        background-color: #f5c6cb;
        color: black;
        padding: 10px;
        border-radius: 5px;
    }
    .title {
        color: #d9534f;
        text-align: center;
        font-size: 30px;
    }
    .subtitle {
        color: #6c757d;
        text-align: center;
        font-size: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">Karuna</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Providing critical help during emergencies</div>', unsafe_allow_html=True)

# Map Integration (Centered on User Location or Wayanad)
def show_map(user_location):
    m = folium.Map(location=user_location, zoom_start=12)
    folium.Marker(
        location=user_location,
        popup="Your Location",
        icon=folium.Icon(color="red")
    ).add_to(m)
    return m

# Function to handle requests and display response
def handle_request(prompt, user_location):
    threading.Thread(target=get_response, args=(prompt, response_queue)).start()
    response = response_queue.get()  # Wait for the response
    st.write(response)
    text_to_speech(response)  # Convert response to speech
    save_to_excel(pd.DataFrame({
        "Timestamp": [datetime.now()],
        "Query": [prompt],
        "Location": [str(user_location)]
    }))

# Get User Location
user_location = get_user_location()

# Expanded Emergency Assistance Options
emergency_options = [
    "I need immediate medical help.",
    "Where is the nearest shelter?",
    "How can I find food?",
    "Give me safety instructions.",
    "How to handle fire accidents?",
    "Emergency evacuation plans.",
    "First aid for injuries.",
    "How to report a missing person?",
    "Guidelines for flood safety.",
    "Power outage assistance."
]

# Display Latitude and Longitude Fields
st.write("Enter your location manually if required:")
latitude = st.text_input("Latitude", value=user_location[0])
longitude = st.text_input("Longitude", value=user_location[1])

# Validate and update user location if manually entered
try:
    user_location = [float(latitude), float(longitude)]
except ValueError:
    st.error("Please enter valid numerical values for latitude and longitude.")

# Quick Pre-Text Response
st.write("Select the type of assistance you need:")
selected_option = st.radio("Quick Responses:", emergency_options)
if st.button("Submit Quick Response"):
    handle_request(selected_option, user_location)

# Custom Text Input for Query
st.write("Or type your query below:")
custom_query = st.text_area("Enter your query:")
if st.button("Submit Custom Query"):
    handle_request(custom_query, user_location)

# Voice Input for Query
st.write("Or use your voice to ask for help:")
if st.button("Record Voice Query"):
    voice_query = voice_to_text()
    st.write(f"You said: {voice_query}")
    handle_request(voice_query, user_location)

# Show Map with User Location
with st.expander("View Map of Your Location"):
    st.write("Here is your detected location:")
    m = show_map(user_location)
    st_folium(m, width=700, height=500)

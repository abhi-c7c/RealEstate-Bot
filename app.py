from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
import urllib.parse
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # Set session timeout (30 minutes)
Session(app)

template = "You are an expert in Airbnb. Answer the following query: {question}"
prompt = ChatPromptTemplate.from_template(template)
model = OllamaLLM(model="llama3.1")
chain = prompt | model

def get_airbnb_location_link(location):
    base_url = "https://www.airbnb.com/s/"
    location_encoded = urllib.parse.quote(location)
    return f'<a href="{base_url}{location_encoded}/homes" target="_blank">Click here for Airbnb listings in {location}</a>'

def get_google_maps_link(location):
    base_url = "https://www.google.com/maps/search/?api=1&query="
    location_encoded = urllib.parse.quote(location)
    return f'<a href="{base_url}{location_encoded}" target="_blank">Click here for Google Maps link of {location}</a>'

def is_location_query(question):
    location_keywords = ["find", "search", "looking for", "location", "place", "stay in"]
    return any(keyword in question.lower() for keyword in location_keywords)

@app.route("/", methods=["GET", "POST"])
def index():
    session.permanent = True

    # Clear conversation if session expired or 'Restart' button clicked
    if 'conversation' not in session or 'last_active' not in session:
        session['conversation'] = []
        session['last_active'] = time.time()

    timeout = 1800  # Session timeout of 30 minutes
    if time.time() - session['last_active'] > timeout:
        session['conversation'] = []

    if request.method == "POST":
        # If "Restart Conversation" button was clicked
        if 'restart' in request.form:
            session['conversation'] = []
            return redirect(url_for('index'))

        question = request.form["question"]

        if is_location_query(question):
            location = question.split("in")[-1].strip()
            airbnb_link = get_airbnb_location_link(location)
            google_maps_link = get_google_maps_link(location)
            response = (
                f"Here is the information for {location}:\n"
                f"{location} is a great destination to find wonderful Airbnb stays and explore nearby areas.\n"
                f"<br><br>{airbnb_link}<br>{google_maps_link}"
            )
        else:
            response = chain.invoke({"question": question})

        session['conversation'].append({"question": question, "response": response})
        session['last_active'] = time.time()  # Update last active time

    conversation = session.get('conversation', [])
    return render_template("index.html", conversation=conversation)



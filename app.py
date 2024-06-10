# Importation des bibliothèques requises
import logging
import time
from flask import Flask, render_template, request, g
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
from flask_mail import Mail, Message
from threading import Thread
from datetime import datetime, timedelta

from keras.models import load_model

from src.get_data import GetData
from src.utils import create_figure, prediction_from_model
import flask_monitoringdashboard as dashboard  # Importation de flask_monitoringdashboard pour monitorer l'utilisation de l'app web

# Configuration du logger
logging.basicConfig(
    filename="error.log",
    level=logging.ERROR,
    format="%(asctime)s:%(levelname)s:%(message)s",
)

app = Flask(__name__)
app.config.update(
    MAIL_SERVER='smtp.example.com',  # Remplacez par votre serveur SMTP
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='your_email@example.com',  # Remplacez par votre email
    MAIL_PASSWORD='your_password',  # Remplacez par votre mot de passe
    MAIL_DEFAULT_SENDER=('Traffic Monitoring', 'your_email@example.com')
)
mail = Mail(app)
dashboard.config.init_from(file="config.cfg")

request_counts = []

# Middleware pour mesurer le temps de réponse
@app.before_request
def start_timer():
    g.start = time.time()

@app.after_request
def log_request(response):
    if hasattr(g, "start"):
        elapsed_time = time.time() - g.start
        logging.info(f"Request to {request.path} took {elapsed_time:.4f} seconds")
    
    now = datetime.now()
    request_counts.append(now)

    # Remove requests older than 1 hour
    one_hour_ago = now - timedelta(hours=1)
    request_counts[:] = [req_time for req_time in request_counts if req_time > one_hour_ago]

    if len(request_counts) > 100:
        send_alert_email()

    return response

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_alert_email():
    msg = Message(
        subject='Alert: High Traffic',
        recipients=['admin@example.com'],  # Remplacez par l'email de l'admin
        body='The application has received over 100 requests in the last hour.'
    )
    Thread(target=send_async_email, args=(app, msg)).start()

# Initialisation de l'objet GetData avec l'URL des données
data_retriever = GetData(
    url="https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets/etat-du-trafic-en-temps-reel/exports/json?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"
)
data = data_retriever()  # Récupération des données

# Chargement du modèle Keras
model = load_model("model.h5")

@app.route("/", methods=["GET", "POST"])
def index():
    try:
        if request.method == "POST":
            # Création de la figure de la carte et conversion en JSON
            fig_map = create_figure(data)
            graph_json = fig_map.to_json()

            # Récupération de l'heure sélectionnée par l'utilisateur
            selected_hour = request.form["hour"]

            # Prédiction à partir du modèle en utilisant l'heure sélectionnée
            cat_predict = prediction_from_model(model, selected_hour)

            # Définition des couleurs et des textes basés sur la prédiction
            color_pred_map = {
                0: ["Prédiction : Libre", "green"],
                1: ["Prédiction : Dense", "orange"],
                2: ["Prédiction : Bloqué", "red"],
            }

            # Rendu du template avec les informations nécessaires
            return render_template(
                "index.html",  # Correction du nom du template
                graph_json=graph_json,
                text_pred=color_pred_map[cat_predict][0],
                color_pred=color_pred_map[cat_predict][1],
            )
        else:
            # Création de la figure de la carte pour les requêtes GET et conversion en JSON
            fig_map = create_figure(data)
            graph_json = fig_map.to_json()  # Appel de la méthode to_json()

            # Rendu du template avec la carte
            return render_template(
                "index.html", graph_json=graph_json
            )  # Correction du nom du template
    except Exception as e:
        logging.error("An error occurred", exc_info=True)
        return "An internal error occurred", 500

dashboard.bind(app)  # Mise en place du monitoring après la définition des routes et avant le lancement de l'app

if __name__ == "__main__":
    app.run(debug=True)

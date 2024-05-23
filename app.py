from flask import Flask, render_template, request
import plotly.graph_objs as go
import plotly.express as px
import numpy as np

from keras.models import load_model

from src.get_data import GetData
from src.utils import create_figure, prediction_from_model
import flask_monitoringdashboard as dashboard # Importation de flask_monitoringdashboard pour monitorer l'utilisation de l'app web

app = Flask(__name__)
dashboard.config.init_from(file='config.cfg')
dashboard.bind(app) # Mise en place du monitoring

# Initialisation de l'objet GetData avec l'URL des données
data_retriever = GetData(
    url="https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets/etat-du-trafic-en-temps-reel/exports/json?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"
)
data = data_retriever()  # Récupération des données

# Chargement du modèle Keras
model = load_model("model.h5")

@app.route("/", methods=["GET", "POST"])
def index():
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
        return render_template("index.html", graph_json=graph_json)  # Correction du nom du template

if __name__ == "__main__":
    app.run(debug=True)

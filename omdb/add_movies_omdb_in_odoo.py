############################################################
#    1) Recupéré 100 films de l'API OMDB                   #
#    2) Les mettre dans Odoo comme produits                #
#    3) Savoir trier les films par genre                   #
#    4) Les mettres disponibles à la vente sur le site web #
############################################################

import base64
import os
import logging
from random import randint
import requests
import erppeek
from movies_list import MOVIES

API_KEY = os.environ.get("OMDB_API_KEY")
BASE_URL = f"http://www.omdbapi.com/?apikey={API_KEY}&"
PARAMS = {
    "t": "title",
}


logging.basicConfig(level=logging.INFO)


def get_image(url):
    """Download image and return as a base64 decode in string"""
    if url == "N/A":
        return False
    try:
        response = requests.get(url)
        img = base64.b64encode(response.content)
        return img.decode("utf-8")
    except requests.RequestException as err:
        logging.error(f"Erreur lors du chargement de l'image: {err}")
        return False


def get_movies(base_url, params, movies_list):
    """Get movie from OMDB API
    Return a list of dict with movies data"""
    err_movie_not_found = {"Response": "False", "Error": "Movie not found!"}
    movies_data = []
    for movie in movies_list:
        params["t"] = movie
        response = requests.get(base_url, params=params).json()
        if response == err_movie_not_found:
            pass
        else:
            movies_data.append(response)
            logging.info("Film trouvé : " + movies_data[-1]["Title"])
    return movies_data


def get_categories(movies_data):
    """Get all categories from movies data"""
    categories = []
    for movie in movies_data:
        categories.append(movie["Genre"])
    return categories


def create_categories(odoo, categories):
    """Create categories in odoo"""
    for category in categories:
        vals = {
            "name": category,
        }
        category_odoo = odoo.model("product.category").browse(
            [("name", "=", category)]
        )
        if not category_odoo:
            odoo.model("product.category").create(vals)
    logging.info("--Categories Ok--")


def get_category_id(odoo, category_name):
    """Get category id from odoo"""
    category = odoo.model("product.category").browse(
        [("name", "=", category_name)]
    )
    if category:
        return category[0]
    return False


def connection_odoo_local():
    """Connect to Odoo local"""
    odoo_url = "http://localhost:8069"
    odoo_db = "proslogiciels_db"
    odoo_username = "admin"
    odoo_password = "admin"
    return erppeek.Client(odoo_url, odoo_db, odoo_username, odoo_password)


def main():
    # Connexion au odoo local
    odoo = connection_odoo_local()

    # Obtenir la liste des films
    movies_data = get_movies(BASE_URL, PARAMS, MOVIES)

    # Obtenir la liste des catégories et les créer dans Odoo
    categories = get_categories(movies_data)
    create_categories(odoo, categories)

    # Mettre les films dans DouDou comme produits
    for movie in movies_data:
        gender = get_category_id(odoo, movie["Genre"])
        poster = get_image(movie["Poster"])
        vals = {
            "name": movie["Title"],
            "list_price": randint(3, 12),
            "image_1920": poster,
            "description": movie["Plot"],
            "year": movie["Year"],
            "categ_id": gender if gender else False,
            "run_time": movie["Runtime"],
            "meta_score": movie["Metascore"],
            "actors": movie["Actors"],
            "default_code": movie["imdbID"],
            "website_published": True,
        }
        # Check si le film existe dans Odoo
        movie_odoo = odoo.model("product.template").browse(
            [("name", "=", movie["Title"])]
        )
        if not movie_odoo:
            odoo.model("product.template").create(vals)
        else:
            movie_odoo.write(vals)


if __name__ == "__main__":
    main()

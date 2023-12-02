# 1) Créer des contacts dans odoo avec une image de profile
# 2) Récupere dans le script l'image du contact
# 3) Envoyer l'image à une IA pour qu'elle nous renvoie une description de la personne
# 4) On écrit la description dans le champ "Note interne" du contact
import os
import logging
import json
import requests
import erppeek


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ODOO_URL = "http://localhost:8069"
ODOO_DB = "proslogiciels_db"
ODOO_USERNAME = "admin"
ODOO_PASSWORD = "admin"

logging.basicConfig(level=logging.INFO)


def connection_odoo_local():
    """Connect to Odoo local"""
    odoo_url = ODOO_URL
    odoo_db = ODOO_DB
    odoo_username = ODOO_USERNAME
    odoo_password = ODOO_PASSWORD
    return erppeek.Client(odoo_url, odoo_db, odoo_username, odoo_password)


def get_profiles(odoo):
    """Get profiles from odoo
    Return a list of dict with id and image_1920"""
    partner_ids = odoo.model("res.partner").search([])
    profiles = []

    for partner_id in partner_ids:
        partner = odoo.model("res.partner").browse(partner_id)
        if not partner.is_company:
            profile_data = {"id": "", "image_1920": ""}
            profile_data["id"] = partner.id
            profile_data["image_1920"] = partner.image_1920
            profiles.append(profile_data)

    return profiles


def ai_analyse_image(profiles):
    """Send image to AI and get a description of the person
    Return a list of dict with partner id and description"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Décris moi cette personne"},
                    {
                        "type": "image_url",
                        "image_url": {"url": ""},
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }

    data_profiles = []
    for profile in profiles:
        payload["messages"][0]["content"][1]["image_url"][
            "url"
        ] = f"data:image/jpeg;base64,{profile['image_1920']}"

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        description = response.json()["choices"][0]["message"]["content"]
        profile["description"] = description
        data_profiles.append(profile)
    return data_profiles


def write_description_to_odoo(odoo, data_profiles):
    """Add description to odoo contact for each profile"""
    for profile in data_profiles:
        partner = odoo.model("res.partner").browse(profile["id"])
        if partner:
            partner.write({"comment": profile["description"]})


def main():
    # Connexion au odoo local
    odoo = connection_odoo_local()

    # Récupération de l'id et image des profiles qui sont des personnes
    profiles = get_profiles(odoo)

    # Obtention de la description
    profiles_descriptions = ai_analyse_image(profiles)
    logging.info("Analyze down")

    # Ecrire la description
    write_description_to_odoo(odoo, profiles_descriptions)
    logging.info("Contact description updated")


if __name__ == "__main__":
    main()

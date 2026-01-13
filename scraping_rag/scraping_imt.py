import requests
from bs4 import BeautifulSoup
import os

# URL du site IMT
URL = "https://www.imt.sn/"

# Dossier de sortie
OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def scrape_imt():
    response = requests.get(URL)
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")

    # Récupérer tout le texte visible
    texts = soup.stripped_strings

    content = "\n".join(texts)

    # Sauvegarde dans un fichier texte
    with open(os.path.join(OUTPUT_DIR, "imt_content.txt"), "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Scraping terminé : imt_content.txt créé")

if __name__ == "__main__":
    scrape_imt()

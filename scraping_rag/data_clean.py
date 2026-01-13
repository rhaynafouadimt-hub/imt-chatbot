import os
import re

INPUT_FILE = "data/imt_content.txt"
OUTPUT_FILE = "data/imt_clean.txt"

REMOVE_WORDS = ["Accueil", "Formations", "Recherche", "Admissions", "Contacts"]

def clean_text(text):
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        # ignorer lignes vides
        if not line:
            continue

        # supprimer mots inutiles
        for word in REMOVE_WORDS:
            line = re.sub(rf"\b{word}\b", "", line, flags=re.IGNORECASE)

        # nettoyer espaces multiples
        line = re.sub(r"\s+", " ", line)

        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)

def main():
    if not os.path.exists(INPUT_FILE):
        print("❌ Fichier source introuvable :", INPUT_FILE)
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    cleaned = clean_text(text)

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print("✅ Nettoyage structuré terminé")

if __name__ == "__main__":
    main()

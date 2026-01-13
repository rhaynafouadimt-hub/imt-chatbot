import os

INPUT_FILE = "data/imt_clean.txt"
OUTPUT_DIR = "data/sections"
os.makedirs(OUTPUT_DIR, exist_ok=True)

KEYWORDS = {
    "formations.txt": ["formation", "licence", "master", "ingénierie"],
    "contacts.txt": ["contact", "adresse", "email", "téléphone"],
    "presentation.txt": ["institut", "imt", "mission", "objectif"]
}

def split_text():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for filename, words in KEYWORDS.items():
        with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as out:
            for line in lines:
                if any(word.lower() in line.lower() for word in words):
                    out.write(line + "\n")

    print("✅ Données séparées par thèmes")

if __name__ == "__main__":
    split_text()

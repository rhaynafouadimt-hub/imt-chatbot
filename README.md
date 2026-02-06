 IMT Chatbot – Projet NLP

Application de chatbot développée avec Chainlit (Python), disposant d’une interface utilisateur personnalisée et d’une mémoire persistante via Redis.
Le projet peut être lancé avec ou sans Docker.

-- Lancement du projet (SANS Docker)
1️. Créer et activer l’environnement virtuel
python -3.10 -m venv venv


Windows

venv\Scripts\activate


Linux / macOS

source venv/bin/activate

2️. Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

3️. Lancer Redis (obligatoire)

Si Redis est installé localement :

redis-server

4️. Lancer l’application Chainlit
chainlit run app.py


 Application accessible sur :
 http://localhost:8000

 Lancement du projet (AVEC Docker – recommandé)
1️. Prérequis

Docker

Docker Compose

2️. Lancer l’application
docker-compose up --build


 Application accessible sur :
 http://localhost:8000

Redis et Chainlit sont lancés automatiquement.

 Fonctionnalités

Interface utilisateur personnalisée (CSS)

Menu de démarrage (starter menu)

Mémoire persistante avec Redis

Gestion des sessions utilisateur

Architecture modulaire :

UI

Memory

Components

 Contexte pédagogique :

Projet réalisé dans le cadre d’un travail académique en NLP / Intelligence Artificielle, avec un focus sur :

la structuration logicielle

l’expérience utilisateur

la persistance des données

l’industrialisation via Docker

 

Étudiant :Fallou Tague

École : IMT

Année académique : 2025–2026

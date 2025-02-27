# OCR ID Card API

## Description
Une API RESTful pour l'extraction automatique d'informations à partir de cartes d'identité utilisant des techniques de OCR (Reconnaissance Optique de Caractères), de reconnaissance faciale et d'intelligence artificielle.

## Fonctionnalités
- Extraction de texte à partir d'images de pièces d'identité
- Reconnaissance et validation faciale
- API RESTful complète avec documentation Swagger
- Intégration avec Google Generative AI pour l'analyse avancée

## Prérequis
- Python 3.10+
- CMake (nécessaire pour dlib/face_recognition)
- Environnement de développement Linux ou macOS recommandé (Windows possible avec configuration supplémentaire)
- Accès à internet pour les API externes (optionnel)

## Installation

### 1. Cloner le dépôt
```bash
git clone https://github.com/amede0430/ocr_id_card_api.git
cd ocr_id_card_api
```

### 2. Créer et activer un environnement virtuel
```bash
python -m venv ocr_env
source ocr_env/bin/activate  # Sur Linux/macOS
# ou
ocr_env\Scripts\activate  # Sur Windows
```

### 3. Installer les dépendances système (Ubuntu/Debian)
```bash
sudo apt install cmake build-essential libboost-all-dev
```

### 4. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### 5. Configuration de la base de données
```bash
python manage.py migrate
```

### 6. Démarrer le serveur de développement
```bash
python manage.py runserver
```

## Utilisation de l'API

### Documentation API
Une fois le serveur démarré, la documentation Swagger est accessible à l'adresse:
```
http://localhost:8000/swagger/
```

### Exemple d'utilisation
```python


url = "http://localhost:8000/api/v1/"
```

## Structure du projet
```
ocr_id_card_api/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── .dockerignore
├── Dockerfile
├── db.sqlite3
├── doc.md
├── yolov8n-face.pt
├── ocr_id_card_api/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── __pycache__/
├── ocr_ci_v1/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── __pycache__/

```

## Principales bibliothèques utilisées
- Django & Django REST framework: Pour l'API REST
- Pillow: Traitement d'images
- PyMuPDF: Extraction de texte à partir de PDF
- face_recognition: Reconnaissance faciale
- ultralytics: Détection d'objets (YOLOv8)
- Google Generative AI: Analyse avancée des documents

## Configuration avancée

### Variables d'environnement
Créez un fichier `.env` à la racine du projet:
```
DEBUG=True
SECRET_KEY=your_secret_key
GOOGLE_API_KEY=your_google_api_key
```

### Configuration de l'API Google
Pour utiliser les fonctionnalités de l'API Google Generative AI:
1. Créez un compte de service Google Cloud Platform
2. Activez l'API Generative AI
3. Créez une clé API et ajoutez-la dans votre fichier `.env`

## Dépannage
- Problèmes avec dlib/face_recognition: Assurez-vous que CMake est correctement installé
- Erreurs de mémoire: Ajustez la taille des images avant traitement

## Contribution
Les contributions sont les bienvenues! N'hésitez pas à ouvrir une issue ou soumettre une pull request.

## Licence
Ce projet est sous licence MIT.
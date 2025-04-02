# myapp/views.py

import json
import re
import os
import base64
from django.conf import settings
import fitz  # PyMuPDF
from PIL import Image, ImageOps
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import FaceVerificationSerializer
from django.core.files.uploadedfile import InMemoryUploadedFile
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from google.api_core.exceptions import ResourceExhausted
import random
import cv2
import numpy as np
import tempfile

import google.generativeai as genai
from ultralytics import YOLO
import face_recognition  # Bibliothèque alternative pour la comparaison faciale

genai.configure(api_key=settings.GOOGLE_GENAI_API_KEY)

class ProcessPDFView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id_document': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY, description='ID card document (PDF or image)'),
                'face_photo': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY, description='Photo of the face to compare'),
            },
            required=['id_document', 'face_photo'],
        ),
        responses={
            200: openapi.Response(
                description='Response with extracted data and verification status',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether the operation was successful'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Status message'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties = {
                                'id_number': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro d'identification"),
                                'first_names': openapi.Schema(type=openapi.TYPE_STRING, description="Prénoms"),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de famille"),
                                'nationality': openapi.Schema(type=openapi.TYPE_STRING, description="Nationalité"),
                                'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING, description="Date de naissance"),
                                'place_of_birth': openapi.Schema(type=openapi.TYPE_STRING, description="Lieu de naissance"),
                                'issuing_authority': openapi.Schema(type=openapi.TYPE_STRING, description="Autorité de délivrance"),
                                'date_of_expiry': openapi.Schema(type=openapi.TYPE_STRING, description="Date d'expiration"),
                                'card_number': openapi.Schema(type=openapi.TYPE_STRING, description="Numéro de la carte"),
                                'verification_result': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Résultat de la vérification faciale"),
                                'similarity_score': openapi.Schema(type=openapi.TYPE_NUMBER, description="Score de similarité entre les visages (distance: plus petit = plus similaire)"),
                            },
                        ),
                        'code': openapi.Schema(type=openapi.TYPE_STRING, description='Status code'),
                    },
                ),
            ),
            400: openapi.Response(
                description='Bad Request',
                examples={
                    'application/json': {
                        'success': False,
                        'message': 'Missing required files or unsupported file type',
                        'code': 'invalid_input'
                    }
                }
            ),
            500: openapi.Response(
                description='Internal Server Error',
                examples={
                    'application/json': {
                        'success': False,
                        'message': 'Failed to process the request',
                        'code': 'processing_error'
                    }
                }
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = FaceVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid input data',
                'code': 'invalid_input',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
            
        id_document = serializer.validated_data['id_document']
        face_photo = serializer.validated_data['face_photo']
        
        # Initialisation des variables
        id_img_path = None
        face_img_path = None
        card_face_path = None
        response_json = None
        
        try:
            # Traitement du document d'identification (carte d'identité)
            if id_document.content_type == 'application/pdf':
                # Traitement du fichier PDF
                doc = fitz.open(stream=id_document.read(), filetype="pdf")
                images = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    images.append(img)

                # On traite la première page
                id_img_path = tempfile.mktemp(suffix='.png')
                images[0].save(id_img_path)
                id_img = cv2.imread(id_img_path)
            elif id_document.content_type.startswith('image/'):
                # Traitement du fichier image
                id_img_path = tempfile.mktemp(suffix='.png')
                with open(id_img_path, 'wb') as f:
                    f.write(id_document.read())
                id_img = cv2.imread(id_img_path)
            else:
                return Response({
                    'success': False,
                    'message': 'Unsupported ID document file type',
                    'code': 'unsupported_file_type',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Traitement de la photo du visage
            if face_photo.content_type.startswith('image/'):
                face_img_path = tempfile.mktemp(suffix='.png')
                with open(face_img_path, 'wb') as f:
                    f.write(face_photo.read())
                face_img = cv2.imread(face_img_path)
            else:
                return Response({
                    'success': False,
                    'message': 'Unsupported face photo file type',
                    'code': 'unsupported_file_type',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extraction du visage de la carte avec YOLO
            try:
                # Charger le modèle YOLOv8 pour la détection de visages
                model = YOLO("yolov8n-face.pt")
                
                # Détection des visages sur la carte d'identité
                results = model(id_img)
                
                # Extraire le premier visage détecté (s'il y en a un)
                for result in results:
                    if len(result.boxes.xyxy) > 0:
                        box = result.boxes.xyxy[0]  # Premier visage détecté
                        x1, y1, x2, y2 = map(int, box[:4])
                        card_face_crop = id_img[y1:y2, x1:x2]  # Extraire le visage
                        
                        # Sauvegarde temporaire du visage
                        card_face_path = tempfile.mktemp(suffix='.jpg')
                        cv2.imwrite(card_face_path, card_face_crop)
            except Exception as e:
                # En cas d'erreur dans la détection de visage
                return Response({
                    'success': False,
                    'message': f'Face detection error on ID card: {str(e)}',
                    'code': 'face_detection_error',
                    'data': None
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Vérifier que nous avons bien détecté un visage sur la carte
            if not card_face_path:
                return Response({
                    'success': False,
                    'message': 'No face detected on the ID card',
                    'code': 'no_face_detected',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Comparaison des visages avec face_recognition
            verification_result = False
            similarity_score = 0.0
            
            try:
                # Charger les images pour la comparaison faciale
                card_face_image = face_recognition.load_image_file(card_face_path)
                user_face_image = face_recognition.load_image_file(face_img_path)
                
                # Extraire les encodages faciaux (caractéristiques)
                card_face_encodings = face_recognition.face_encodings(card_face_image)
                user_face_encodings = face_recognition.face_encodings(user_face_image)
                
                # Vérifier si des visages ont été détectés dans les deux images
                if not card_face_encodings or not user_face_encodings:
                    return Response({
                        'success': False,
                        'message': 'Could not detect faces clearly in one or both images',
                        'code': 'face_detection_failed',
                        'data': None
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculer la distance (similitude) entre les visages
                face_distance = face_recognition.face_distance([card_face_encodings[0]], user_face_encodings[0])[0]
                
                # Convertir la distance en score de similitude (0 à 1, où 1 est parfaitement similaire)
                similarity_score = 1 - face_distance
                
                # Seuil de similarité
                similarity_threshold = 0.5
                verification_result = similarity_score >= similarity_threshold
                
            except Exception as e:
                # On continue même en cas d'erreur de comparaison, mais on note l'échec
                verification_result = False
                similarity_score = 0.0
            
            # Analyse de l'image de la carte avec Gemini
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = """Veuillez analyser l'image de la carte d'identité jointe et extraire les informations suivantes :  
                        1. **ID Number** : Le numéro d'identification unique sur la carte.  
                        3. **First Names** : Les prénoms du titulaire de la carte.  
                        4. **Last Name** : Le nom de famille du titulaire.  
                        5. **Nationality** : La nationalité du titulaire.  
                        6. **Date of Birth** : La date de naissance du titulaire.  
                        7. **Place of Birth** : Le lieu de naissance du titulaire.  
                        8. **Issuing Authority** : L'autorité qui a délivré la carte.  
                        9. **Date of Expiry** : La date d'expiration de la carte.  
                        10. **Card Number** : Le numéro de la carte d'identité.  

                        Retournez les informations extraites au **format JSON pur**, sans aucun formatage ou commentaire supplémentaire. Assurez-vous que la sortie soit un JSON valide pour éviter toute erreur de parsing.

                        Si certaines informations ne peuvent pas être trouvées sur l'image, veuillez retourner le JSON avec des champs vides comme indiqué ci-dessous :  

                        {
                            "id_number": "",
                            "first_names": "",
                            "last_name": "",
                            "nationality": "",
                            "date_of_birth": "",
                            "place_of_birth": "",
                            "issuing_authority": "",
                            "date_of_expiry": "",
                            "card_number": ""
                        }
                        """
            
            extracted_data = {
                "id_number": "",
                "first_names": "",
                "last_name": "",
                "nationality": "",
                "date_of_birth": "",
                "place_of_birth": "",
                "issuing_authority": "",
                "date_of_expiry": "",
                "card_number": ""
            }
            
            try:
                response = None
                has_resource_exhausted_error = True
                i = 1
                
                while has_resource_exhausted_error and i < 30:
                    try:
                        has_resource_exhausted_error = False
                        # Utiliser l'image de la carte d'identité pour l'extraction des données
                        response = model.generate_content([prompt, Image.open(id_img_path)])
                    except ResourceExhausted:
                        genai.configure(api_key=random.choice(settings.GOOGLE_GENAI_API_KEYS))
                        has_resource_exhausted_error = True
                        i += 1
                
                if response:
                    cleaned_response = re.sub(r'```json|```', '', response.text).strip()
                    extracted_data = json.loads(cleaned_response)
            except Exception as e:
                # On continue même en cas d'erreur d'extraction, avec les valeurs par défaut
                pass
            
            # Construction du dictionnaire de réponse
            response_json = {
                "id_number": extracted_data.get("id_number", ""),
                "first_names": extracted_data.get("first_names", ""),
                "last_name": extracted_data.get("last_name", ""),
                "nationality": extracted_data.get("nationality", ""),
                "date_of_birth": extracted_data.get("date_of_birth", ""),
                "place_of_birth": extracted_data.get("place_of_birth", ""),
                "issuing_authority": extracted_data.get("issuing_authority", ""),
                "date_of_expiry": extracted_data.get("date_of_expiry", ""),
                "card_number": extracted_data.get("card_number", ""),
                "verification_result": verification_result,
                "similarity_score": round(similarity_score, 3)
            }
            
            # Déterminer le message et le code de statut
            if verification_result:
                message = "Face verification successful and data extracted"
                code = "success"
                status_code = status.HTTP_200_OK
            else:
                message = "Face verification failed but data was extracted"
                code = "verification_failed"
                status_code = status.HTTP_200_OK  # On retourne quand même 200 car l'extraction a fonctionné
            
            return Response({
                'success': True,
                'message': message,
                'data': response_json,
                'code': code
            }, status=status_code)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to process the request: {str(e)}',
                'code': 'processing_error',
                'data': response_json if response_json else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        finally:
            # Nettoyage des fichiers temporaires
            for temp_file in [id_img_path, face_img_path, card_face_path]:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
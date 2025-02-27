# myapp/serializers.py



from rest_framework import serializers

class FaceVerificationSerializer(serializers.Serializer):
    id_document = serializers.FileField(
        help_text="Document d'identité (PDF ou image)"
    )
    face_photo = serializers.FileField(
        help_text="Photo du visage à comparer"
    )
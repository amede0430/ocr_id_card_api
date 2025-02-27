# myapp/urls.py

from django.urls import path
from .views import ProcessPDFView

urlpatterns = [
    path('v1/', ProcessPDFView.as_view(), name='process_pdf'),
]

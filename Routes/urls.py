
from django.urls import path, include
from .views import GenerativeAIText

urlpatterns = [
    path('askAI/',GenerativeAIText.as_view(),name='AI Query')
]

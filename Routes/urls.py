
from django.urls import path, include
from .views import QueryView

urlpatterns = [
    path('askAI/',QueryView.as_view(),name='AI Query')
]

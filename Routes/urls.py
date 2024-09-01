
from django.urls import path, include
from .views import *

urlpatterns = [
    path('conversations/', ConversationList.as_view(), name='conversation-list'),
    path('api/conversations/<int:pk>/', ConversationDetail.as_view(), name='conversation-detail'),
    path('api/messages/', MessageList.as_view(), name='message-list'),
    path('askAI/',GenerativeAIText.as_view(),name='AI Query'),
    path('api/register/', register_user, name='register'),
    path('api/chatActivity/', ChatActivityAPIView.as_view(), name='chat-activity'),
    path('api/trafficStats/', TrafficStatsAPIView.as_view(), name='traffic-stats'),
    path('api/pageViews/', PageViewStatsAPIView.as_view(), name='page-view-stats'),
    path('api/trackPageView/', TrackPageViewAPIView.as_view(), name='track-page-view'),
]

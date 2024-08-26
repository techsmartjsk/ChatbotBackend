from rest_framework.views import APIView
from django.conf import settings
import json
import openai
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Conversation, Message
from .serializer import ConversationSerializer, MessageSerializer
from .models import *
from django.utils import timezone
from django.utils.timezone import now
import uuid

class TrackPageViewAPIView(APIView):
    def post(self, request):
        url = request.data.get('url')
        user_agent = request.data.get('user_agent')
        ip_address = request.META.get('REMOTE_ADDR', '')
        session_id = request.session.session_key or uuid.uuid4().hex
        request.session.save()

        if not url:
            return Response({'error': 'URL is required'}, status=status.HTTP_400_BAD_REQUEST)

        existing_view = PageView.objects.filter(
            url=url,
            ip_address=ip_address,
            session_id=session_id,
            timestamp__gte=now() - timezone.timedelta(minutes=1)  # Adjust as needed
        ).exists()

        if not existing_view:
            PageView.objects.create(
                url=url,
                user_agent=user_agent,
                ip_address=ip_address,
                session_id=session_id
            )

        return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
    
class PageViewStatsAPIView(APIView):
    def get(self, request):
        total_views = PageView.objects.count()

        data = {
            'total_views': total_views
        }
        return Response(data)

class TrafficStatsAPIView(APIView):
    def get(self, request):
        total_views = PageView.objects.count()

        data = {
            'total_views': total_views
        }
        return Response(data)

class ChatActivityAPIView(APIView):
    def get(self, request):
        today = timezone.now().date()
        active_conversations = Conversation.objects.filter(created_at__date=today)
        total_messages = Message.objects.filter(conversation__in=active_conversations).count()
        total_conversations = active_conversations.count()

        data = {
            'total_conversations': total_conversations,
            'total_messages': total_messages
        }
        return Response(data)

class ConversationList(APIView):
    def get(self, request):
        user = request.user
        conversations = Conversation.objects.filter(models.Q(user1=user) | models.Q(user2=user))
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConversationDetail(APIView):
    def get(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)

class MessageList(APIView):
    def get(self, request):
        conversation_id = request.query_params.get('conversation')
        if not conversation_id:
            return Response({'error': 'Conversation ID required'}, status=status.HTTP_400_BAD_REQUEST)

        messages = Message.objects.filter(conversation_id=conversation_id)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GenerativeAIText(APIView):
    def get_openai_response(self, question):
        openai.api_key = settings.OPENAI_API_KEY
        
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI Assistant about Hotbot Studios. Fetch all details about Hotbot Studios from internet! Add AI Development as our one of the service if someone ask to list our services!"},
                {"role": "user", "content": question}
            ],
            max_tokens=100,
            temperature=0.7,
        )
        
        answer = response['choices'][0]['message']['content']
        return answer.strip()
    def post(self, request):
        question = request.data['question']
        generated_ai_response = self.get_openai_response(question)
        results = {
            "response": generated_ai_response 
        }
        return HttpResponse(json.dumps(results), content_type='application/json')

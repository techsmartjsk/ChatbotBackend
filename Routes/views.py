from rest_framework.views import APIView
from django.conf import settings
import json
import openai
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Conversation, Message
from .serializer import ConversationRequestSerializer, ConversationResponseSerializer, MessageRequestSerializer, MessageResponseSerializer, UserRegistrationSerializer, PageSerializer
from .models import *
from django.utils import timezone
from django.utils.timezone import now
import uuid
import os
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_token(request):
    user = request.user  # Get the user from the request
    user_info = {
        "email": user.email,
        "name": user.name,
    }
    return Response({
        "status": "Token is valid",
        "user_info": user_info
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(email=email, password=password)
    
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user':user.name,
            'id':user.pk
        }, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user_id = user.id 
        return Response({'id': user_id}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def chat(request):
    email = request.data['email']
    name = request.data['name']

    try:
        user = ChatUser.objects.get(email=email)
    except ChatUser.DoesNotExist:
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_id = user.id 
            return Response({'id': user_id}, status=status.HTTP_201_CREATED)

    return Response({
        'id': user.id
    }, status=status.HTTP_200_OK)

class TrackPageViewAPIView(APIView):
    def get(self, request):
        pages = PageView.objects.all()
        serialised_pages = PageSerializer(pages, many=True)

        return Response(serialised_pages.data, status=status.HTTP_200_OK)
    

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
        conversations = Conversation.objects.all()
        serializer = ConversationResponseSerializer(conversations, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.data["user2"] == "AI":
            request.data["user2"] = ChatUser.objects.get(email="hotlinedigital@gmail.com").pk

        serializer = ConversationRequestSerializer(data=request.data)
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

        serializer = ConversationResponseSerializer(conversation)
        return Response(serializer.data)

class MessageList(APIView):
    def get(self, request):
        conversation_id = request.query_params.get('conversation')
        if not conversation_id:
            messages = Message.objects.all()
            message_serializer = MessageResponseSerializer(messages, many=True)
            return Response(message_serializer.data, status=status.HTTP_200_OK)

        messages = Message.objects.filter(conversation_id=conversation_id)
        serializer = MessageResponseSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.data["sender"] == "AI":
            request.data["sender"] = ChatUser.objects.get(email="hotlinedigital@gmail.com").pk
        serializer = MessageRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GenerativeAIText(APIView):
    document_content = None 

    @classmethod
    def load_document(cls):
        if cls.document_content is None:
            file_path = os.path.join(settings.BASE_DIR,'static', 'hotbot_studios_info.txt')
            print('File path',file_path)
            
            with open(file_path, 'r', encoding='latin-1') as file:
                cls.document_content = file.read()

    def get_openai_response(self, question):
        self.load_document()
        openai.api_key = settings.OPENAI_API_KEY

        print("OPENAI API KEY", settings.OPENAI_API_KEY)
        
        system_message = "You are an AI Assistant about Hotbot Studios. Your name is Harsh Bot. Fetch all details about Hotbot Studios from the internet! Add AI Development as one of our services if someone asks to list our services! Connect with the Agent if the user asks for it, reply only : Sure connecting you to our customer support team! All the answers should be in maximum 50 words."

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "system", "content": self.document_content},
                {"role": "user", "content": question}
            ],
            max_tokens=200,
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

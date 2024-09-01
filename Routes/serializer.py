from rest_framework import serializers
from .models import Conversation, Message, ChatUser, PageView

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = ChatUser
        fields = ('email', 'name', 'password')

    def create(self, validated_data):
        user = ChatUser(
            email=validated_data['email'],
            name=validated_data['name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
class MessageRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'timestamp']

class MessageResponseSerializer(serializers.ModelSerializer):
    sender = UserRegistrationSerializer()

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'timestamp']

class ConversationRequestSerializer(serializers.ModelSerializer):
    messages = MessageResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user1', 'user2', 'messages']

class ConversationResponseSerializer(serializers.ModelSerializer):
    messages = MessageResponseSerializer(many=True, read_only=True)
    user1 = UserRegistrationSerializer()
    user2 = UserRegistrationSerializer()

    class Meta:
        model = Conversation
        fields = ['id', 'user1', 'user2', 'messages']

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageView
        fields = ['id', 'url', 'ip_address', 'user_agent']

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PageView(models.Model):
    url = models.URLField()
    timestamp = models.DateTimeField(default=timezone.now)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)

class Conversation(models.Model):
    user1 = models.ForeignKey(User, related_name='conversations1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='conversations2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    def __str__(self):
        return f'Conversation between {self.user1.username} and {self.user2.username}'
    
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from .models import Conversation, ChatUser, Message
        
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        from .models import Conversation, ChatUser, Message

        text_data_json = json.loads(text_data)
        message = text_data_json.get('content')
        sender_id = text_data_json.get('sender')

        if not message or not sender_id:
            await self.send(text_data=json.dumps({
                'error': 'Invalid message format'
            }))
            return

        try:
            conversation = await database_sync_to_async(Conversation.objects.get)(id=self.conversation_id)
            chat_user = await database_sync_to_async(ChatUser.objects.get)(id=sender_id)
            await database_sync_to_async(Message.objects.create)(conversation=conversation, sender=chat_user, content=message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': chat_user.email
                }
            )
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'content': message,
            'sender': sender
        }))

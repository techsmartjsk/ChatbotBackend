from django.contrib import admin
from .models import *

admin.site.register(Message)
admin.site.register(Conversation)
admin.site.register(PageView)
admin.site.register(ChatUser)
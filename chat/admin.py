from typing import List

from django.contrib import admin

from .models import Chat, Room, Shout, ShoutBox


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ["room_id", "author", "friend"]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["room_id", "author", "friend"]


@admin.register(Shout)
class ShoutAdmin(admin.ModelAdmin):
    list_display = ["shoutbox", "author", "date"]


@admin.register(ShoutBox)
class ShoutBoxAdmin(admin.ModelAdmin):
    list_display = ["shoutbox_id", "shoutbox_name"]

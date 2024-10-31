from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from users.forms import UserRegisterForm
from users.models import BlockList, Profile, Relationship


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "verified")


class CustomUserAdmin(UserAdmin):
    add_form = UserRegisterForm


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Relationship)
admin.site.register(BlockList)

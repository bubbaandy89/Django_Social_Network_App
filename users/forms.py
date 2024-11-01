import os
from typing import List

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from PIL import Image
from PIL.ImageFile import ImageFile

from users.models import Profile
from users.validators import validate_email


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(validators=[validate_email])

    class Meta:
        model = User
        fields: List[str] = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields: List[str] = ["first_name", "last_name", "username", "email"]


class ProfileUpdateForm(forms.ModelForm):
    x = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height = forms.FloatField(widget=forms.HiddenInput(), required=False)

    image = forms.ImageField(
        label=("Image for your profile"),
        error_messages={"invalid": ("Image files only")},
        widget=forms.FileInput,
        required=True,
    )

    class Meta:
        model = Profile
        fields: List[str] = [
            "date_of_birth",
            "bio",
            "how_did_you_hear_about_us",
            "facebook_link",
            "instagram_link",
            "twitter_link",
            "image",
        ]

    """Saving Cropped Image"""

    def save(self, *args, **kwargs):
        img = super(ProfileUpdateForm, self).save(*args, **kwargs)

        x = self.cleaned_data.get("x")
        y = self.cleaned_data.get("y")
        w = self.cleaned_data.get("width")
        h = self.cleaned_data.get("height")

        if x and y and w and h:
            image: ImageFile = Image.open(img.image)
            cropped_image: Image.Image = image.crop((x, y, w + x, h + y))
            resized_image: Image.Image = cropped_image.resize(
                (300, 300), Image.Resampling.LANCZOS
            )
            if img.image.path != os.path.join(settings.MEDIA_ROOT, "default.jpg"):
                resized_image.save(img.image.path)

        return img

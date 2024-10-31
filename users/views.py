from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models import QuerySet
from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView

from django_social.utils import URLValidator, new_user_created_email, send_welcome_email
from friend.friend_request_status import FriendRequestStatus
from friend.models import FriendList, FriendRequest
from friend.utils import get_friend_request_or_false
from notification.models import Notification
from users.forms import ProfileUpdateForm, UserRegisterForm, UserUpdateForm
from users.models import Profile


@receiver(user_logged_in)
def got_online(sender: Any, request: HttpRequest, **kwargs: Any) -> None:
    """
    Signal receiver that sets user's profile to online when they log in.

    Args:
        sender: The sender of the signal
        user: The user who logged in
        request: The current request object
        **kwargs: Additional keyword arguments
    """
    if not request.user.is_authenticated:
        raise PermissionError("User must be authenticated")

    try:
        user_profile: Profile = Profile.objects.get(user=request.user)

        # Ensure the user can only modify their own profile
        if user_profile.user != request.user:
            raise PermissionError("Cannot modify another user's profile")

        user_profile.is_online = True
        user_profile.save()
    except Profile.DoesNotExist:
        # Handle case where profile doesn't exist
        pass


@receiver(user_logged_out)
def got_offline(sender: Any, request: HttpRequest, **kwargs: Any) -> None:
    """
    Signal receiver that sets user's profile to offline when they log out.

    Args:
        sender: The sender of the signal
        user: The user who logged out
        request: The current request object
        **kwargs: Additional keyword arguments
    """
    if not request.user.is_authenticated:
        raise PermissionError("User must be authenticated")

    try:
        user_profile: Profile = Profile.objects.get(user=request.user)

        # Ensure the user can only modify their own profile
        if user_profile.user != request.user:
            raise PermissionError("Cannot modify another user's profile")

        user_profile.is_online = False
        user_profile.save()
    except Profile.DoesNotExist:
        # Handle case where profile doesn't exist
        pass


@login_required
def follow_unfollow_profile(request: HttpRequest) -> HttpResponse:
    """
    View to handle following and unfollowing users.

    Args:
        request: The HTTP request object

    Returns:
        HttpResponse: Redirects to the previous page or profile list
    """
    if request.method == "POST":
        my_profile: Profile = Profile.objects.get(user=request.user)
        pk: str = request.POST.get("profile_pk", "")
        obj: Profile = Profile.objects.get(pk=pk)

        if obj.user in my_profile.following.all():
            my_profile.following.remove(obj.user)
        else:
            my_profile.following.add(obj.user)
            Notification.objects.create(
                sender=request.user, user=obj.user, notification_type=2
            )
        # Redirect back to the calling page
        next_url = request.META.get("HTTP_REFERER")
        safe_url: str = URLValidator.validate_redirect(next_url, request)
        return redirect(safe_url)
    # Not a POST so lets redirect to the profile list view
    return redirect("profile-list-view")


def register(request: HttpRequest) -> HttpResponse:
    """
    View for user registration.

    Args:
        request: The HTTP request object

    Returns:
        HttpResponse: Rendered registration page or redirect to login
    """
    if request.method == "POST":
        form: UserRegisterForm = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username: Optional[str] = form.cleaned_data.get("username")
            user_email: Optional[str] = form.cleaned_data.get("email")
            if not username or not user_email:
                return redirect("register")
            messages.success(
                request,
                f"Your account has been created! You can login now {username}",
            )

            profile_url: str = (
                f"{settings.PROTOCOL}://{settings.SITE_DOMAIN}/user/public-profile/{username}/"
            )
            send_welcome_email(
                user_email=user_email,
                username=username,
                profile_url=profile_url,
            )
            new_user_created_email(
                user_email=user_email,
                username=username,
                profile_url=profile_url,
            )
            return redirect("login")
        messages.error(request, "Invalid form data. Please try again.")
    else:
        form = UserRegisterForm()
    return render(request, "users/register.html", {"form": form})


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """
    View for user profile management.

    Args:
        request: The HTTP request object

    Returns:
        HttpResponse: Rendered profile page
    """
    context: Dict[str, Any] = {}
    if request.method == "POST":
        u_form = UserUpdateForm(request.POST, instance=request.user)  # type:ignore
        p_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile  # type:ignore
        )

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your account has been updated!")
            return redirect("profile")
        p_form = ProfileUpdateForm(instance=request.user.profile)  # type:ignore

        context = {"u_form": u_form, "p_form": p_form}
    return render(request, "users/profile.html", context)


def public_profile(request: HttpRequest, username: str) -> HttpResponse:
    """
    View for public profile display.

    Args:
        request: The HTTP request object
        username: Username of the profile to display

    Returns:
        HttpResponse: Rendered public profile page
    """
    user: User = User.objects.get(username=username)
    return render(request, "users/public_profile.html", {"cuser": user})


class ProfileListView(LoginRequiredMixin, ListView):
    """View for displaying all user profiles."""

    model = Profile
    template_name = "users/all_profiles.html"
    context_object_name = "profiles"
    paginate_by: int = 20

    def get_queryset(self) -> QuerySet[Profile]:
        """Get all profiles except the current user's."""
        return Profile.objects.all().exclude(user=self.request.user)

    def render_to_response(
        self, context: dict[str, Any], **response_kwargs
    ) -> HttpResponse:
        """
        Custom render response to check user verification.

        Args:
            context: The template context

        Returns:
            HttpResponse: Rendered response or redirect
        """
        userobj: Profile = Profile.objects.get(id=self.request.user.id)  # type: ignore
        if not userobj.verified:
            return redirect("profile")
        return super().render_to_response(context)


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """View for displaying detailed user profile information."""

    model = Profile
    template_name = "users/user_profile_details.html"
    context_object_name = "profiles"

    def get_queryset(self) -> QuerySet[Profile]:
        """Get all profiles except the current user's."""
        return Profile.objects.all().exclude(user=self.request.user)

    def get_object(self, queryset=None) -> Profile:
        """Get the profile object based on the URL parameter."""
        pk = self.kwargs.get("pk")
        return Profile.objects.get(pk=pk)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get the context data for the template.

        Returns:
            dict: Context data including friend status and following information
        """
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        view_profile: Profile = self.get_object()
        my_profile: Profile = Profile.objects.get(user=self.request.user)

        # Following status
        context["follow"] = view_profile.user in my_profile.following.all()

        # Friend list handling
        account: User = view_profile.user
        friend_list: FriendList
        friend_list, _ = FriendList.objects.get_or_create(user=account)
        friends: QuerySet[User] = friend_list.friends.all()
        context["friends"] = friends

        # Friend request status
        user: User = self.request.user  # type: ignore
        is_self: bool = True
        is_friend: bool = False
        request_sent: int = FriendRequestStatus.NO_REQUEST_SENT
        friend_requests: Optional[QuerySet[FriendRequest]] = None

        if user.is_authenticated and user != account:
            is_self = False
            is_friend = friends.filter(pk=user.id).exists()  # type: ignore

            if not is_friend:
                if friend_request := get_friend_request_or_false(
                    sender=account, receiver=user
                ):
                    context["pending_friend_request_id"] = friend_request.pk

                elif get_friend_request_or_false(sender=user, receiver=account):
                    request_sent = FriendRequestStatus.YOU_SENT_TO_THEM
        elif not user.is_authenticated:
            is_self = False
        else:
            friend_requests = FriendRequest.objects.filter(
                receiver=user, is_active=True
            )

        context.update(
            {
                "request_sent": request_sent,
                "is_friend": is_friend,
                "is_self": is_self,
                "friend_requests": friend_requests,
            }
        )

        return context

    def render_to_response(
        self, context: dict[str, Any], **response_kwargs
    ) -> HttpResponse:
        """
        Custom render response to check user verification.

        Args:
            context: The template context

        Returns:
            HttpResponse: Rendered response or redirect
        """
        userobj: Profile = Profile.objects.get(id=self.request.user.id)  # type: ignore
        if not userobj.verified and self.request.user != self.get_object().user:
            return redirect("profile")
        return super().render_to_response(context)

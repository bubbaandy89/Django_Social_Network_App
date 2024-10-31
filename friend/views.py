import json
from typing import Any, Dict, Optional

from django.contrib.auth.models import User
from django.db.models.manager import BaseManager
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from friend.models import FriendList, FriendRequest


def friends_list_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    context: Dict[str, Any] = {}
    user = request.user
    if user.is_authenticated:
        user_id = kwargs.get("user_id")
        if user_id:
            try:
                this_user: User = User.objects.get(pk=user_id)
                context["this_user"] = this_user
            except User.DoesNotExist:
                return HttpResponse("That user does not exist.")
            try:
                friend_list: FriendList = FriendList.objects.get(user=this_user)
            except FriendList.DoesNotExist:
                return HttpResponse(
                    f"Could not find a friends list for {this_user.username}"
                )

            # Must be friends to view a friends list
            if user != this_user:
                if user not in friend_list.friends.all():
                    return HttpResponse(
                        "You must be friends to view their friends list."
                    )
            friends: list[tuple[User, bool]] = (
                []
            )  # [(friend1, True), (friend2, False), ...]
            # get the authenticated user's friend list
            auth_user_friend_list: FriendList = FriendList.objects.get(user=user)
            for friend in friend_list.friends.all():
                friends.append((friend, auth_user_friend_list.is_mutual_friend(friend)))
            context["friends"] = friends
    else:
        return HttpResponse("You must be friends to view their friends list.")
    return render(request, "friend/friend_list.html", context)


def friend_requests(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    context: Dict[str, Any] = {}
    user = request.user
    if user.is_authenticated:
        user_id: Optional[str] = kwargs.get("user_id")
        account: User = User.objects.get(pk=user_id)
        if account == user:
            friend_requests: BaseManager[FriendRequest] = FriendRequest.objects.filter(
                receiver=account, is_active=True
            )
            context["friend_requests"] = friend_requests
        else:
            return HttpResponse("You can't view another users friend requets.")
    else:
        redirect("login")
    return render(request, "friend/friend_requests.html", context)


def send_friend_request(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    user = request.user
    payload: Dict[str, str] = {}
    if request.method == "POST" and user.is_authenticated:
        user_id: Optional[str] = request.POST.get("receiver_user_id")
        if user_id:
            receiver: User = User.objects.get(pk=user_id)
            try:
                friend_requests: BaseManager[FriendRequest] = (
                    FriendRequest.objects.filter(sender=user, receiver=receiver)
                )
                try:
                    for friend_request in friend_requests:
                        if friend_request.is_active:
                            raise Exception("You already sent them a friend request.")
                    friend_request = FriendRequest(sender=user, receiver=receiver)
                    friend_request.save()
                    payload["response"] = "Friend request sent."
                except Exception as e:
                    payload["response"] = str(e)
            except FriendRequest.DoesNotExist:
                friend_request = FriendRequest(sender=user, receiver=receiver)
                friend_request.save()
                payload["response"] = "Friend request sent."

            if payload["response"] is None:
                payload["response"] = "Something went wrong."
        else:
            payload["response"] = "Unable to sent a friend request"
    else:
        payload["response"] = "You must be authenticated to send a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def accept_friend_request(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    user = request.user
    payload: Dict[str, str] = {}
    if request.method == "GET" and user.is_authenticated:
        friend_request_id: Optional[str] = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request: FriendRequest = FriendRequest.objects.get(
                pk=friend_request_id
            )
            # confirm that is the correct request
            if friend_request.receiver == user:
                if friend_request:
                    # Accepting the founded request
                    friend_request.accept()
                    payload["response"] = "Friend request accepted."

                else:
                    payload["response"] = "Something went wrong."
            else:
                payload["response"] = "That is not your request to accept."
        else:
            payload["response"] = "Unable to accept that friend request."
    else:
        payload["response"] = "You must be authenticated to accept a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def remove_friend(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    user = request.user
    payload: Dict[str, str] = {}
    if request.method == "POST" and user.is_authenticated:
        user_id: Optional[str] = request.POST.get("receiver_user_id")
        if user_id:
            try:
                removee: User = User.objects.get(pk=user_id)
                friend_list: FriendList = FriendList.objects.get(user=user)
                friend_list.unfriend(removee)
                payload["response"] = "Successfully removed that friend."
            except Exception as e:
                payload["response"] = f"Something went wrong: {str(e)}"
        else:
            payload["response"] = "There was an error. Unable to remove that friend."
    else:
        payload["response"] = "You must be authenticated to remove a friend."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def decline_friend_request(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    user = request.user
    payload: Dict[str, str] = {}
    if request.method == "GET" and user.is_authenticated:
        friend_request_id: Optional[str] = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request: FriendRequest = FriendRequest.objects.get(
                pk=friend_request_id
            )
            # confirm that is the correct request
            if friend_request.receiver == user:
                if friend_request:
                    # Declining the founded request
                    friend_request.decline()
                    payload["response"] = "Friend request declined."
                else:
                    payload["response"] = "Something went wrong."
            else:
                payload["response"] = "That is not your friend request to decline."
        else:
            payload["response"] = "Unable to decline that friend request."
    else:
        payload["response"] = "You must be authenticated to decline a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def cancel_friend_request(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    user = request.user
    payload: Dict[str, str] = {}
    if request.method == "POST" and user.is_authenticated:
        user_id: Optional[str] = request.POST.get("receiver_user_id")
        if user_id:
            receiver = User.objects.get(pk=user_id)
            try:
                friend_requests: BaseManager[FriendRequest] = (
                    FriendRequest.objects.filter(
                        sender=user, receiver=receiver, is_active=True
                    )
                )

                # There should only ever be one active friend request at any given time.
                # Cancel them all just in case.
                if len(friend_requests) > 1:
                    for friend_request in friend_requests:
                        friend_request.cancel()
                    payload["response"] = "Friend request cancelled."
                else:
                    # Cancelling the first request
                    if friend_request := friend_requests.first():
                        friend_request.cancel()
                        payload["response"] = "Friend request cancelled."
            except FriendRequest.DoesNotExist:
                payload["response"] = (
                    "Nothing to cancel. Friend request does not exist."
                )

        else:
            payload["response"] = "Unable to cancel that friend request."
    else:
        payload["response"] = "You must be authenticated to cancel a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")

from typing import Literal, Union

from friend.models import FriendRequest


def get_friend_request_or_false(
    sender, receiver
) -> Union[FriendRequest, Literal[False]]:
    try:
        return FriendRequest.objects.get(
            sender=sender, receiver=receiver, is_active=True
        )
    except FriendRequest.DoesNotExist:
        return False

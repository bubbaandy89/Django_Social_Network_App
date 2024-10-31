from django.contrib.auth.models import User
from django.db import models

""" FriendList model """


class FriendList(models.Model):
    user: models.OneToOneField = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="user"
    )
    friends: models.ManyToManyField = models.ManyToManyField(
        User, blank=True, related_name="friends"
    )

    def __str__(self) -> str:
        return self.user.username

    def add_friend(self, account) -> None:
        if account not in self.friends.all():
            self.friends.add(account)
            self.save()

    def remove_friend(self, account) -> None:
        if account in self.friends.all():
            self.friends.remove(account)
            self.save()

    def unfriend(self, removee) -> None:
        remover_friends_list = self
        remover_friends_list.remove_friend(removee)

        friends_list: FriendList = FriendList.objects.get(user=removee)
        friends_list.remove_friend(self.user)

    def is_mutual_friend(self, friend) -> bool:
        if friend in self.friends.all():
            return True
        return False


""" Friend Request model """


class FriendRequest(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="receiver"
    )
    is_active = models.BooleanField(blank=True, null=True, default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.sender.username

    def accept(self):
        # update both sender and receiver friend list
        receiver_friend_list: FriendList = FriendList.objects.get(user=self.receiver)
        if receiver_friend_list:
            receiver_friend_list.add_friend(self.sender)
            sender_friend_list: FriendList = FriendList.objects.get(user=self.sender)
            if sender_friend_list:
                sender_friend_list.add_friend(self.receiver)
                self.is_active = False
                self.save()

    def decline(self) -> None:
        self.is_active = False
        self.save()

    def cancel(self) -> None:
        self.is_active = False
        self.save()

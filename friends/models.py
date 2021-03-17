from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from authentication.models import User


# Create your models here.
class FriendList(models.Model):
    user = models.OneToOneField('authentication.User', on_delete=models.CASCADE, related_name="user")
    friends = models.ManyToManyField('authentication.User', related_name="friends", blank=True)

    def __str__(self):
        return self.user.username

    # for adding new friend
    def add_friend(self, account):
        self.friends.add(account)

    # for removing friends 
    def remove_friends(self, account):
        self.friends.remove(account)

    # removee is the person who is being removed from friendlist
    # Unfriend function
    def unfriend(self, removee):
        self.remove_friends(removee)
        friend_list = FriendList.objects.filter(user = removee).first()
        if friend_list:
            friend_list.remove_friends(self.user)

class FriendRequest(models.Model):
    sender = models.ForeignKey('authentication.User', on_delete=models.CASCADE , related_name="sender")
    receiver = models.ForeignKey('authentication.User', on_delete=models.CASCADE , related_name="receiver")
    is_active = models.BooleanField(blank=True, null=False, default=True)
    time_stamp = models.DateTimeField(auto_now=True)

    def get_sender(self):
        sender = self.sender
        if sender:
            return sender.username
        return ''

    def __str__(self):
        return f"{self.sender.username} sent request to {self.receiver.username}"

    # called when a request is accepted
    def accept(self):
        receiver_friend_list, created = FriendList.objects.get_or_create(user_id=self.receiver_id)
        receiver_friend_list.add_friend(self.sender)
        sender_friend_list, created = FriendList.objects.get_or_create(user_id=self.sender_id)
        sender_friend_list.add_friend(self.receiver)
        self.is_active=False
        self.save()

    # called when a friendlist is declined
    def decline(self):
        self.is_active = False
        self.save()

    # called dwhen sender cancel the friend request
    def cancel(self):
        self.is_active = False
        self.save()


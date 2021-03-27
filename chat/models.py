from UtkarshBackend import settings
from chat.managers import ThreadManager
from django.db import models


class TrackingModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Thread(TrackingModel):
    THREAD_TYPE = (
        ('personal', 'Personal'),
        ('group', 'Group')
    )

    name = models.CharField(max_length=50, null=True, blank=True)
    thread_type = models.CharField(max_length=15, choices=THREAD_TYPE, default='group')
    users = models.ManyToManyField('authentication.User')

    objects = ThreadManager()

    def __str__(self) -> str:
        if self.thread_type == 'personal' and self.users.count() == 2:
            return f'{self.users.first()} and {self.users.last()}'
        return f'{self.name}'

class Message(TrackingModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    sender = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    text = models.TextField(blank=False, null=False)
    timestamp = models.DateTimeField(auto_now=True)


    def __str__(self) -> str:
        return f'From <Thread - {self.thread}>'

    def get_sender_user(self):
        sender = self.sender
        if sender:
            return sender.username
        return ''

class BackupMessage(TrackingModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    sender = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    text = models.TextField(blank=False, null=False)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'From <Thread - {self.thread}>'


class ConnectionHistory(models.Model):
    ONLINE = 'online'
    OFFLINE = 'offline'
    STATUS = (
        (ONLINE, 'On-line'),
        (OFFLINE, 'Off-line'),
    )
    user = models.ForeignKey('authentication.User',on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10, choices=STATUS,
        default=ONLINE
    )
    last_seen = models.DateTimeField(null=True, blank= True)


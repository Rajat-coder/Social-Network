from django.db import models
from django.db.models import Count

class ThreadManager(models.Manager):
    def get_or_create_personal_thread(self, user1, user2):
        thread = self.get_queryset().annotate(u_count = Count('users')).filter(
            u_count=2, thread_type='personal', users__id=user1.id
        ).filter(users__id = user2.id).first()
        if thread is None:
            thread = self.create(thread_type='personal')
            thread.users.add(user1, user2)
        return thread

    def by_user(self, user):
        return self.get_queryset().filter(users__in = [user]).distinct()


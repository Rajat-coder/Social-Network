from rest_framework import serializers
from authentication.models import User
from friends.models import *


class User_Serializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=("id",'first_name', 'last_name','profile_image','username')

class FriendListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendList
        fields="__all__"


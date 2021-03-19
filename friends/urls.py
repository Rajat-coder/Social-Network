from django.urls import path
from friends.views import *

app_name="friend"

urlpatterns=[
    path('userprofile/', UserSearch.as_view()),
    path('sendrequest/', RequestSend.as_view()),
    path('requestslist/received/', ReceivedFriendRequestList.as_view()),
    path('requestslist/sent/', SentFriendRequestList.as_view()),
    path('acceptrequest/', AcceptRequest.as_view()),
    path('removefriend/', RemoveFriend.as_view()),
    path('declinerequest/', DeclineRequest.as_view()),
    path('cancelrequest/', CancelRequest.as_view()),
    path("friendlist/", FriendListApi.as_view())
]


from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from authentication.models import User
from authentication.utils import validate_phone
from friends.models import FriendRequest
from friends.serializers import *
from friends.utils import *
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status

class UserSearch(APIView):
    def get(self, request):
        user = request.user
        username = request.GET.get('username', '')
        is_self = False
        is_friend = False
        user_data = {}
        pending_request_id = None
        Request_already_sent = False
        res_status=status.HTTP_400_BAD_REQUEST
        output_status=False
        output_detail="Invalid Username"
        if username:
            getdata = User.objects.filter(username = username).first()
            if getdata is None:
                phone = validate_phone(username)['phone']
                if phone:
                    getdata = User.objects.filter(mobile = phone).first()
            if getdata is None:
                getdata = User.objects.filter(email = username).first()
            if getdata:
                res_status=status.HTTP_200_OK
                output_status=True
                output_detail="User found"
                user_data = User_Serializer(getdata).data
                friend_list, created = FriendList.objects.get_or_create(user_id = getdata.id)
                if user == getdata:
                    is_self = True
                if (not created) and (user != getdata) and friend_list.friends.all().filter(pk = user.id).first():
                    is_friend = True
                pending_request = FriendRequest.objects.filter(sender=getdata, receiver=user, is_active=True).first()
                if pending_request:
                    pending_request_id = pending_request.id
                req_sent = FriendRequest.objects.filter(sender=user, receiver=getdata, is_active=True).first()
                if req_sent:
                    Request_already_sent = True

        context = {
            'status': output_status,
            'detail': output_detail,
            'data': {
                'is_self': is_self,
                'is_friend': is_friend,
                'user_data': user_data,
                'pending_request_id': pending_request_id,
                'Request_already_sent': Request_already_sent,
            }
        }
        return Response(context, status = res_status)

class RequestSend(APIView):
    def post(self,request):
        user = request.user
        receiver_user_id = request.data.get("receiver_user_id")
        res_status=status.HTTP_400_BAD_REQUEST
        output_status=False
        output_detail="Unable to send chat request"
        if receiver_user_id:
            receiver = User.objects.filter(id = receiver_user_id).first()
            if receiver:
                # Get all active friend requests
                friend_requests = FriendRequest.objects.filter(sender_id = user.id, receiver_id = receiver.id, is_active = True)
                friend_request = friend_requests.first()
                if friend_request:
                    friend_requests.update(is_active = False)
                    friend_request.is_active = True
                    friend_request.save()
                else:
                    # If none are active create a new friend request
                    friend_request = FriendRequest(sender=user, receiver=receiver)
                    friend_request.save()
                res_status=status.HTTP_200_OK
                output_status=True
                output_detail="Chat request sent successfully"
                try:
                    req_sent_noti(friend_request.receiver_id, user.get_full_name())
                except Exception as e:
                    pass
        payload={
            "status":output_status,
            "detail":output_detail
        }
        return Response(payload,status=res_status)

class SentFriendRequestList(APIView):
    paginate_by = 20
    def get(self,request):
        user = request.user
        page = request.GET.get('page', '')
        try:
            page = int(page)
        except Exception as  e:
            page = 1
        friend_requests = list(FriendRequest.objects.select_related("receiver").filter(
            sender_id = user.id, is_active = True
        ).order_by('-id')[self.paginate_by * (page - 1):self.paginate_by * page+1])
        output_data = []
        next_exist = (len(friend_requests) == (self.paginate_by+1))
        friend_requests = friend_requests[:self.paginate_by]
        for i in friend_requests:
            receiver_data = User_Serializer(i.receiver).data
            output_data.append({
                'id': i.id,
                'receiver': receiver_data,
            }) 

        context = {
            "status":True,
            "detail":"Success",
            "data":output_data,
            "next_exist": next_exist,
        }
        return Response(context)

class ReceivedFriendRequestList(APIView):
    paginate_by = 20
    def get(self,request):
        user = request.user
        page = request.GET.get('page', '')
        try:
            page = int(page)
        except Exception as  e:
            page = 1
        friend_requests = list(FriendRequest.objects.select_related("sender").filter(
            receiver_id = user.id, is_active = True
        ).order_by('-id')[self.paginate_by * (page - 1):self.paginate_by * page+1])
        output_data = []
        next_exist = (len(friend_requests) == (self.paginate_by+1))
        friend_requests = friend_requests[:self.paginate_by]
        for i in friend_requests:
            sender_data = User_Serializer(i.sender).data
            output_data.append({
                'id': i.id,
                'sender': sender_data,
            }) 

        context = {
            "status":True,
            "detail":"Success",
            "data":output_data,
            "next_exist": next_exist,
        }
        return Response(context)

class AcceptRequest(APIView):
    def post(self, request):
        user = request.user
        payload = {}
        friend_request_id = request.data.get("request_id")
        res_status=status.HTTP_400_BAD_REQUEST
        output_status=False
        output_detail="Unable to accept chat request"
        if friend_request_id:
            friend_request = FriendRequest.objects.filter(id=friend_request_id, receiver_id=user.id, is_active=True).first()
            if friend_request:
                # found the request. Now accept it
                friend_request.accept()
                try:
                    req_accpt_noti(friend_request.sender_id, user.get_full_name())
                except Exception as e:
                    pass
                res_status = status.HTTP_200_OK
                output_status=True
                output_detail="Friend request accepted"
        payload = {
            "status":output_status,
            "detail":output_detail
        }
        return Response(payload, status=res_status)

class RemoveFriend(APIView):
    def post(self,request):
        user = request.user
        receiver_user_id = request.data.get("receiver_user_id")
        res_status=status.HTTP_400_BAD_REQUEST
        output_status=False
        output_detail="Unable to remove friend"
        if receiver_user_id:
            removee = User.objects.get(id=receiver_user_id)
            friend_list = FriendList.objects.filter(user = user).first()
            if friend_list:
                friend_list.unfriend(removee)
                res_status=status.HTTP_200_OK
                output_status=True
                output_detail="Successfully removed friend"
        payload = {
            "status":output_status,
            "detail":output_detail
        }
        return Response(payload, status=res_status)

class DeclineRequest(APIView):
    def post(self,request):
        user = request.user
        friend_request_id = request.data.get("friend_request_id")
        res_result=status.HTTP_400_BAD_REQUEST
        output_status=False
        output_detail="Unable to decline chat request"
        if friend_request_id:
            friend_cnt = FriendRequest.objects.filter(id=friend_request_id, receiver_id=user.id, is_active=True).update(is_active=False)
            # There should only ever be ONE active friend request at any given time. Cancel them all just in case.
            if friend_cnt > 0:
                res_result = status.HTTP_200_OK
                output_status=True
                output_detail="Friend request decline"
        payload={
            "status":output_status,
            "detail":output_detail
        }
        return Response(payload,status=res_result)

class CancelRequest(APIView):
    def post(self,request):
        user = request.user
        user_id = request.data.get("receiver_user_id")
        res_result=status.HTTP_400_BAD_REQUEST
        output_status=False
        output_detail="Unable to cancel chat request"
        if user_id:
            friend_cnt = FriendRequest.objects.filter(sender_id=user.id, receiver_id=user_id, is_active=True).update(is_active=False)
            # There should only ever be ONE active friend request at any given time. Cancel them all just in case.
            if friend_cnt>0 :
                res_result=status.HTTP_200_OK
                output_status=True
                output_detail="Friend request cancelled"
        payload={
            "status":output_status,
            "detail":output_detail
        }
        return Response(payload,status=res_result)

class FriendListApi(APIView):
    def get(self, request):
        user = request.user
        
        friend_list = FriendList.objects.filter(user = user).first()
        output_data=[]
        if friend_list:
            output_data=User_Serializer(friend_list.friends.all(),many=True).data
        context={
            "status":True,
            "detail":"Success",
            "data":output_data,
        }
        return Response(context)



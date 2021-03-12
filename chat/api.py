from django.Response import Response

class Chatview(APIView):
    paginate_by = 25

    def get(self,request):
        last = request.GET.get('last', None)
        # Logged in user
        user = request.user
        # Other user
        other_user_id = request.GET.get('other_user_id')
        other_user = None
        user_data, last_seen_data, msgs_data = {}, {}, []
        res_status = status.HTTP_400_BAD_REQUEST
        output_status = False
        output_detail = "Invalid user id"
        if other_user_id:
            other_user = User.objects.filter(id=other_user_id).first()
        if other_user:
            obj = Thread.objects.get_or_create_personal_thread(user, other_user)
            if not last:
                user_data = UserChatSerializer(other_user).data
                last_seen = ConnectionHistory.objects.get(user_id = other_user.id)
                last_seen_data = ConnectionHistorySerializer(last_seen).data

            # Thread messages
            if last:
                msgs = obj.message_set.filter(id__lt = last)
            else:
                msgs = obj.message_set.all()
            msgs = msgs.exclude(sender_id = user.id).order_by('-id')[:self.paginate_by]
            msgs_data = Message_Serializer(msgs, many = True).data
            last = None
            query_count = len(msgs)
            if query_count > 0 and query_count == self.paginate_by:
                last = output_data[query_count - 1].id
            Message.objects.filter(id__in = list(msgs.values_list('id', flat = True))).delete()
            res_status = status.HTTP_200_OK
            output_status = True
            output_detail = "Success"

        output = {
            'status': output_status,
            'detail': output_detail,
            'data': {
                'other_user': user_data,
                'last_seen': last_seen_data,
                'messages': msgs_data,
                'last': last,
            }
        }
        return Response(output, status = res_status)


from django.Response import Response

class Chatview(APIView):
    paginate_by = 25

    def get(self,request):
        last = request.GET.get('last', None)
        # Logged in user
        user = request.user
        # Other user
        other_user_id = request.GET.get('other_user_id')
        other_user = None
        user_data, last_seen_data, msgs_data = {}, {}, []
        res_status = status.HTTP_400_BAD_REQUEST
        output_status = False
        output_detail = "Invalid user id"
        if other_user_id:
            other_user = User.objects.filter(id=other_user_id).first()
        if other_user:
            obj = Thread.objects.get_or_create_personal_thread(user, other_user)
            if not last:
                user_data = UserChatSerializer(other_user).data
                last_seen = ConnectionHistory.objects.get(user_id = other_user.id)
                last_seen_data = ConnectionHistorySerializer(last_seen).data

            # Thread messages
            if last:
                msgs = obj.message_set.filter(id__lt = last)
            else:
                msgs = obj.message_set.all()
            msgs = msgs.exclude(sender_id = user.id).order_by('-id')[:self.paginate_by]
            msgs_data = Message_Serializer(msgs, many = True).data
            last = None
            query_count = len(msgs)
            if query_count > 0 and query_count == self.paginate_by:
                last = output_data[query_count - 1].id
            Message.objects.filter(id__in = list(msgs.values_list('id', flat = True))).delete()
            res_status = status.HTTP_200_OK
            output_status = True
            output_detail = "Success"

        output = {
            'status': output_status,
            'detail': output_detail,
            'data': {
                'other_user': user_data,
                'last_seen': last_seen_data,
                'messages': msgs_data,
                'last': last,
            }
        }
        return Response(output, status = res_status)



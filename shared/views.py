from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from authentication.models import User, SanghPosition
from authentication.utils import has_category_access, check_user_approval_access
from django.core.cache import cache

from rest_framework.decorators import api_view, renderer_classes, parser_classes, permission_classes
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, NotFound, MethodNotAllowed
# Create your views here.

# Not a view but a util function to get user from request
def get_user_object(request, allow_admin_access = True):
    user = request.user
    uid = request.data.get('uid', request.GET.get('uid', None))
    if uid:
        # if allow_admin_access and user.is_admin:
        #     user = User.objects.filter(id = uid).first()
        #     if user:
        #         return user
        if request.method == 'GET':
            sanghposition = SanghPosition.objects.filter(user_id = uid, is_present = True).select_related('user', 'ikai_dayitva', 'location').first()
            if sanghposition and check_user_approval_access(user, sanghposition.ikai_dayitva, sanghposition.location):
                user = sanghposition.user
            else:
                error_detail = "You don't have access to user: {}".format(uid)
                raise NotFound(detail = error_detail)
    return user

class UserDetailsAPIView(APIView):
    ModelClass = None
    ModelSerializerClass = None
    user_field_name = 'user'
    filter_data = {}
    get_allow_any = False
    allow_admin_access = True
    allow_update = True
    object_name = None
    max_object_count = None
    exempt_category_check = False
    select_related_fields = []
    prefetch_related_fields = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ModelClass:
            raise ValueError('ModelClass field cannot be None')
        if not self.ModelSerializerClass:
            raise ValueError('ModelSerializerClass field cannot be None')

    def check_category_access(self, user):
        if self.exempt_category_check:
            return None
        if self.object_name is None or has_category_access(user, self.object_name):
            return None
        return Response({
            'status' : False,
            'detail': "Disallowed Category - User cannot access these details",
        }, status=status.HTTP_401_UNAUTHORIZED, content_type="application/json")

    def check_object_count(self, user):
        if self.max_object_count is not None:
            obj_count = self.ModelClass.objects.filter(**{self.user_field_name: user}).count()
            if obj_count >= self.max_object_count:
                return Response({
                    'status' : False,
                    'detail': "Maximum {} count reached - Cannot create more objects".format(self.object_name),
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY, content_type="application/json")
        return None

    def get_filter_data(self, request, *args, **kwargs):
        return self.filter_data
    
    def get_queryset(self, request, user, *args, **kwargs):
        object_id = request.GET.get('id', None)
        filter_data = self.get_filter_data(request, *args, **kwargs)
        if not self.get_allow_any:
            filter_data[self.user_field_name] = user
        if object_id:
            filter_data['id'] = object_id
        query = self.ModelClass.objects.filter(**filter_data)
        if self.select_related_fields:
            query = query.select_related(*self.select_related_fields)
        if self.prefetch_related_fields:
            query = query.prefetch_related(*self.prefetch_related_fields)
        return query

    def update_list_output(self, request, output):
        return output

    def update_id_output(self, request, output):
        return output

    def get(self, request, *args, **kwargs):
        user = get_user_object(request, self.allow_admin_access)
        category_check = self.check_category_access(user)
        if category_check:
            return category_check

        output_status = True
        output_detail = "success"
        output_data = None
        res_status = status.HTTP_200_OK
        
        object_id = request.GET.get('id', None)
        model_obj_list = self.get_queryset(request, user, *args, **kwargs)
        if object_id:
            model_obj = model_obj_list.first()
            if model_obj:
                output_data = self.ModelSerializerClass(model_obj, context={'request': request}).data
            else:
                output_status = False
                output_detail = "Invalid Object ID"
                res_status = status.HTTP_400_BAD_REQUEST
        else:
            output_data = self.ModelSerializerClass(model_obj_list, many=True, context={'request': request}).data
        output = {
            'status' : output_status,
            'detail': output_detail,
            'data': output_data
        }
        if object_id:
            output = self.update_id_output(request, output)
        else:
            output = self.update_list_output(request, output)
        return Response(output, status=res_status, content_type="application/json")

    def get_extra_data(self, request, user):
        return {
            self.user_field_name: user.id,
        }
    
    def get_default_object(self, request, user):
        return None

    def create_succes(self, request, obj, output_data, *args, **kwargs):
        return output_data
    
    def update_succes(self, request, obj, output_data, *args, **kwargs):
        return output_data
    
    def post(self, request, *args, **kwargs):
        user = get_user_object(request, self.allow_admin_access)
        category_check = self.check_category_access(user)
        if category_check:
            return category_check

        object_id = request.data.get('id', None)
        if self.allow_update:
            object_ins = self.get_default_object(request, user)
        else:
            object_id = None
            object_ins = None

        if object_ins is None:
            if object_id:
                # Update request
                try:
                    filter_data = {
                        "id": object_id,
                        self.user_field_name: user,
                    }
                    object_ins = self.ModelClass.objects.filter(**filter_data).first()
                except:
                    object_ins = None
            else:
                # Create request
                # object_count_check = self.check_object_count(user)
                # if object_count_check:
                #     return object_count_check
                pass
        else:
            # Update request
            pass

        object_ser = None
        output_status = False
        output_detail = "Invalid details"
        res_status = status.HTTP_400_BAD_REQUEST
        extra_data = self.get_extra_data(request, user)
        if object_ins:
            object_ser = self.ModelSerializerClass(object_ins, data = request.data, extra_data = extra_data, partial = True)
        else:
            if object_id:
                output_detail = "Invalid Object ID"
            else:
                object_ser = self.ModelSerializerClass(data = request.data, extra_data = extra_data)
        if object_ser and object_ser.is_valid():
            output_status = True
            obj = object_ser.save()
            obj_name = 'Object'
            if self.object_name:
                obj_name = self.object_name.capitalize()
            output_data = object_ser.data
            if object_ins:
                output_data = self.update_succes(request, obj, output_data, *args, **kwargs)
                output_detail = '{} updated successfully'.format(obj_name)
                res_status = status.HTTP_202_ACCEPTED
            else:
                output_data = self.create_succes(request, obj, output_data, *args, **kwargs)
                output_detail = '{} added successfully'.format(obj_name)
                res_status = status.HTTP_201_CREATED
            output = {
                'status': output_status,
                'detail': output_detail,
                'data': output_data,
            }
        else:
            output = {
                'status': output_status,
                'detail': output_detail,
            }
            if object_ser:
                output['errors'] = object_ser.errors
        return Response(output, status=res_status, content_type="application/json")


class PaginateDetailsAPIView(APIView):
    ModelClass = None
    ModelSerializerClass = None
    filter_data = {}
    paginate_by = 10
    select_related_fields = []
    prefetch_related_fields = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ModelClass:
            raise ValueError('ModelClass field cannot be None')
        if not self.ModelSerializerClass:
            raise ValueError('ModelSerializerClass field cannot be None')

    def get_filter_data(self, request, *args, **kwargs):
        return self.filter_data
    
    def get_model_class(self, request, *args, **kwargs):
        return self.ModelClass
    
    def get_serializer_class(self, request, *args, **kwargs):
        return self.ModelSerializerClass
    
    def get_queryset(self, request, *args, **kwargs):
        filter_data = self.get_filter_data(request, *args, **kwargs)
        model = self.get_model_class(request, *args, **kwargs)
        if filter_data is None:
            return model.objects.none()
        query = model.objects.filter(**filter_data)
        if self.select_related_fields:
            query = query.select_related(*self.select_related_fields)
        if self.prefetch_related_fields:
            query = query.prefetch_related(*self.prefetch_related_fields)
        return query

    def update_output(self, request, output):
        return output

    def get_last_value(self, obj):
        if obj:
            return str(obj.id)
        return None

    def paginate_query(self, request, query):
        last = request.GET.get('last', None)
        if last:
            query = query.filter(id__lt = last)
        query = query.order_by('-id')[:self.paginate_by]
        return query

    def get(self, request, *args, **kwargs):
        query = self.get_queryset(request, *args, **kwargs)
        query = self.paginate_query(request, query)

        last = None
        query_count = len(query)
        if query_count > 0 and query_count == self.paginate_by:
            last = self.get_last_value(query[query_count - 1])

        serializer_class = self.get_serializer_class(request, *args, **kwargs)
        output_data = serializer_class(query, many=True, context={ 'request': request, }).data
        output_status = True
        output_detail = "success"
        res_status = status.HTTP_200_OK
        output = {
            'status' : output_status,
            'detail': output_detail,
            'data': output_data,
            'last': last,
        }
        # import json
        # print(json.dumps(output, indent = 4))
        
        output = self.update_output(request, output)
        return Response(output, status=res_status, content_type="application/json")


class DropdownAPIView(APIView):
    ModelClass = None
    ModelSerializerClass = None
    serializer_fields = []
    object_name = None
    exempt_cache = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ModelClass:
            raise ValueError('ModelClass field cannot be None')
        if not (self.ModelSerializerClass or self.serializer_fields):
            raise ValueError('Atleast one of serializer_fields or ModelSerializerClass must be specified')

    def check_category_access(self, user):
        if self.object_name is None or has_category_access(user, self.object_name):
            return None
        return Response({
            'status' : False,
            'detail': "Disallowed Category - User cannot access these details",
        }, status=status.HTTP_401_UNAUTHORIZED, content_type="application/json")

    def get_exempt_cache(self, request, *args, **kwargs):
        return self.exempt_cache

    def get_queryset(self, request, *args, **kwargs):
        return self.ModelClass.objects.all()

    def get_serializer_class(self, request, *args, **kwargs):
        return self.ModelSerializerClass
    
    def get_serializer_fields(self, request, *args, **kwargs):
        return self.serializer_fields
    
    def get_serialized_output(self, request, *args, **kwargs):
        model_obj_list = self.get_queryset(request, *args, **kwargs)
        serializer_class = self.get_serializer_class(request, *args, **kwargs)
        if serializer_class:
            return serializer_class(model_obj_list, many=True, context={'request': request}).data
        serializer_fields = self.get_serializer_fields(request, *args, **kwargs)
        if serializer_fields:
            try:
                out = list(model_obj_list.values(*serializer_fields))
                return out
            except Exception as e:
                pass
        return list(model_obj_list.values())
    
    def update_list_output(self, request, output):
        return output

    def get(self, request, *args, **kwargs):
        user = request.user
        category_check = self.check_category_access(user)
        if category_check:
            return category_check

        class_name = self.__class__.__name__
        output_status = True
        output_detail = "success"
        res_status = status.HTTP_200_OK
        print(class_name)
        if self.get_exempt_cache(request, *args, **kwargs):
            output_data = self.get_serialized_output(request, *args, **kwargs)
            print("cache not used")
        else:
            output_data = cache.get(class_name)
            if output_data is None:
                output_data = self.get_serialized_output(request, *args, **kwargs)
                cache.set(class_name, output_data)
                print("not in cache")

        output = {
            'status' : output_status,
            'detail': output_detail,
            'data': output_data
        }
        output = self.update_list_output(request, output)
        return Response(output, status=res_status, content_type="application/json")

    def post(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

        user = request.user
        output_status = True
        output_detail = "success"
        output_data = None
        res_status = status.HTTP_200_OK

        if not user.is_admin:
            output = {
                'status' : False,
                'detail': "User cannot access these details",
                'data': output_data
            }
            return Response(output, status=res_status, content_type="application/json")

        category_check = self.check_category_access(user)
        if category_check:
            return category_check

        object_id = request.data.get('id', None)
        object_ins = None
        if object_id:
            try:
                filter_data = {
                    "id": object_id,
                }
                object_ins = self.ModelClass.objects.filter(**filter_data).first()
            except:
                object_ins = None
        object_ser = None
        output_status = False
        output_detail = "Invalid details"
        res_status = status.HTTP_400_BAD_REQUEST
        if object_ins:
            object_ser = self.ModelSerializerClass(object_ins, data = request.data, partial = True)
        else:
            if object_id:
                output_detail = "Invalid Object ID"
            else:
                object_ser = self.ModelSerializerClass(data = request.data)
        if object_ser and object_ser.is_valid():
            output_status = True
            object_ser = object_ser.save()
            obj_name = 'Object'
            if self.object_name:
                obj_name = self.object_name.capitalize()
            if object_ins:
                output_detail = '{} updated successfully'.format(obj_name)
                res_status = status.HTTP_202_ACCEPTED
            else:
                output_detail = '{} added successfully'.format(obj_name)
                res_status = status.HTTP_201_CREATED
            output = {
                'status': output_status,
                'detail': output_detail,
            }
        else:
            output = {
                'status': output_status,
                'detail': output_detail,
            }
            if object_ser:
                output['errors'] = object_ser.errors
        return Response(output, status=res_status, content_type="application/json")



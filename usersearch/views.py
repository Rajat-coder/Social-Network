from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from authentication.models import *
from authentication.serializers import SanghDayitvaSerializer
from rest_framework import status
from authentication.utils import *
from shared.views import DropdownAPIView
from django.core.files.storage import DefaultStorage

default_storage = DefaultStorage()
user_category_dict = dict(User.CATEGORY)

class UserSearch(APIView):
    fields_map = {
        "user": ["mobile","email","username","blood_group","category","referral_code","gender"],
        "address": ["pincode", "state_id",],
        "profession": ["profession_type", "occupation_type",],
        "sangh": ["join_year", "praant_id",],
        "education": ["education_type", "course_id", "institution_id",],
        "sangheducation": ["type",],
        "sanghposition": ["join_year", "ikai_dayitva_id", "location_id", "ikai_id", "dayitva_id",],
    }
    paginate_by = 50

    def filter_by_education(self,request, user_qs):
        filter_data = {}
        for f in self.fields_map['education']:
            curr = request.GET.get('education__'+f)
            if curr:
                filter_data[f] = curr
        if filter_data:
            user_ids = Education.objects.filter(**filter_data).values_list('user_id', flat = True)
            return user_qs.filter(id__in = user_ids)
        return user_qs

    def filter_by_address(self,request, user_qs):
        filter_data = {}
        for f in self.fields_map['address']:
            curr = request.GET.get('address__'+f)
            if curr:
                filter_data[f] = curr
        if filter_data:
            user_ids = Address.objects.filter(**filter_data).values_list('user_id', flat = True)
            return user_qs.filter(id__in = user_ids)
        return user_qs

    def filter_by_profession(self,request, user_qs):
        filter_data = {}
        for f in self.fields_map['profession']:
            curr = request.GET.get('profession__'+f)
            if curr:
                filter_data[f] = curr
        if filter_data:
            user_ids = Profession.objects.filter(**filter_data).values_list('user_id', flat = True)
            return user_qs.filter(id__in = user_ids)
        return user_qs
    
    def filter_by_sangh(self,request, user_qs):
        filter_data = {}
        for f in self.fields_map['sangh']:
            curr = request.GET.get('sangh__'+f)
            if curr:
                filter_data[f] = curr
        if filter_data:
            user_ids = Sangh.objects.filter(**filter_data).values_list('user_id', flat = True)
            return user_qs.filter(id__in = user_ids)
        return user_qs
    
    def filter_by_sangheducation(self,request, user_qs):
        filter_data = {}
        for f in self.fields_map['sangheducation']:
            curr = request.GET.get('sangheducation__'+f)
            if curr:
                filter_data[f] = curr
        if filter_data:
            user_ids = SanghEducation.objects.filter(**filter_data).values_list('user_id', flat = True)
            return user_qs.filter(id__in = user_ids)
        return user_qs

    def get_user_queryset(self,request):
        user = request.user
        users = User.objects.none()
        sanghposition = SanghPosition.objects.filter(user = user, is_present = True).select_related('location', 'ikai_dayitva').prefetch_related('ikai_dayitva__adjacent_nodes').first()

        if user.orange_tick and sanghposition:
            location = sanghposition.location
            ikai_dayitva = sanghposition.ikai_dayitva.adjacent_nodes.all()
            if request.GET.get("sanghposition__ikai_dayitva_id"):
                ikai_dayitva=ikai_dayitva.filter(id=request.GET.get("sanghposition__ikai_dayitva_id"))
            if request.GET.get("sanghposition__ikai_id"):
                ikai_dayitva=ikai_dayitva.filter(ikai_id=request.GET.get("sanghposition__ikai_id"))
            if request.GET.get("sanghposition__dayitva_id"):
                ikai_dayitva=ikai_dayitva.filter(dayitva_id=request.GET.get("sanghposition__dayitva_id"))

            # ikai_level = ikai_dayitva.aggregate(Max('ikai__ordering')).get('ikai__ordering__max', None)
            if request.GET.get("sanghposition__location_id"):
                children_nodes = DayitvaLocation.objects.filter(id=request.GET.get("sanghposition__location_id"))
            else:
                upbasti_ikai = Ikai.objects.filter(name = 'Upbasti').first()
                ikai_level = upbasti_ikai.ordering if upbasti_ikai else None
                children_nodes = get_location_childrens(location, ikai_level)
            ikai_dayitva = list(ikai_dayitva)
            # position = SanghPosition.objects.none()
            if ikai_dayitva and children_nodes:
                filter_data = {
                    'ikai_dayitva__in': ikai_dayitva,
                    'user__imp_info__in': children_nodes,
                    'is_present': True,
                }
                if request.GET.get("sanghposition__join_year"):
                    filter_data["join_year"]=request.GET.get("sanghposition__join_year")
                user_ids = list(SanghPosition.objects.filter(
                    **filter_data
                ).exclude(user_id = user.id).values_list('user_id',flat=True))
                user_filter = {
                    'id__in': user_ids,
                }
                for f in self.fields_map['user']:
                    curr = request.GET.get(f)
                    if curr:
                        user_filter[f] = curr
                if 'mobile' in user_filter:
                    valid_phone = validate_phone(user_filter['mobile']).get('phone', '')
                    if valid_phone:
                        user_filter['mobile'] = valid_phone
                users = User.objects.filter(**user_filter)
                if request.GET.get('gender') != GENDER.FEMALE:
                    users = users.exclude(gender = GENDER.FEMALE)
        return users

    def get(self,request):
        context = {}
        user = request.user
        if user.orange_tick == True and user.referral_code == '1925':
            user_qs = self.get_user_queryset(request)
            output_data = []
            user_cnt = 0
            page = max(int(request.GET.get('page', 1)), 1)
            if user_qs.exists():
                user_qs = self.filter_by_address(request, user_qs)
                user_qs = self.filter_by_education(request, user_qs)
                user_qs = self.filter_by_profession(request, user_qs)
                user_qs = self.filter_by_sangh(request, user_qs)
                user_qs = self.filter_by_sangheducation(request, user_qs)
                if page == 1:
                    user_cnt = user_qs.count()

                user_qs = user_qs.order_by('-id')[((page - 1) * self.paginate_by):(page * self.paginate_by)]
                output_data = user_qs.values(
                    'id', 'username', 'first_name', 'last_name', 'category', 'date_joined', 'profile_image',
                    'imp_info_id', 'blue_tick', 'orange_tick', 'referral_code',
                )
                for u in output_data:
                    u['category'] = {
                        'key': u['category'],
                        'value': user_category_dict[u['category']]
                    }
                    u['profile_image'] = default_storage.url(u['profile_image'])
            context = {
                'status': True,
                'detail': 'success',
                'data': output_data,
                'page_size': self.paginate_by,
                'count': user_cnt,
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            context = {
                'status': False,
                'detail': 'fail',
                'data': [],
                'page_size': self.paginate_by,
                'count': 0,
            }
            return Response(context, status=status.HTTP_403_FORBIDDEN)


class DayitvaListView(DropdownAPIView):
    ModelClass = SanghDayitva
    ModelSerializerClass = SanghDayitvaSerializer
    # serializer_fields = ['id', 'name',]


from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.serializers import *
from authentication.models import *

phone = "917856565600"
api_key = "123"
user_data = {
    "first_name": "Lipsum First Name",
    "last_name": "Lipsum Last Name",
    "email": "lipsum@utkarsh.app",
    "referral_code": "123456",
    "dob": "2000-08-25",
    "category": "Others",
}
admin_phone = "919876543210"
admin_user_data = {
    "first_name": "Lipsum First Name",
    "last_name": "Lipsum Last Name",
    "email": "lipsum@utkarsh.app",
    "referral_code": "123456",
    "dob": "2000-08-25",
    "category": "Others",
}

class LoginTestCase(APITestCase):
    validate_phone_url = reverse("authentication:validate_phone")
    validate_otp_url = reverse("authentication:validate_otp")
    user_url = reverse("authentication:user_details")
    admin_user_test = False

    def setUp(self):
        super().setUp()
        data = user_data
        user = User.objects.create_user(username = phone, password = 'password')
        login_phone = phone
        serializer = RegisterUserSerializer(user, data=data)
        serializer.is_valid()
        self.user = serializer.save()
        if self.admin_user_test:
            admin_user = User.objects.create_user(username = admin_phone, password = 'password')
            login_phone = admin_phone
            serializer = RegisterUserSerializer(admin_user, data=admin_user_data)
            serializer.is_valid()
            admin_user = serializer.save()
            admin_user.is_admin = True
            admin_user.save()

        data = {
            "phone": login_phone,
            "api_key": api_key,
        }
        response = self.client.post(self.validate_phone_url, data = data)

        otp_code = response.json()['data']['otp_code']
        data = {
            "phone": login_phone,
            "is_login": True,
            "api_key": api_key,
            "otp_code": otp_code,
        }
        response = self.client.post(self.validate_otp_url, data = data)

        self.refresh = response.json()['data']['refresh']
        self.access = response.json()['data']['access']
        self.api_authentication()

    def api_authentication(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access)

class UserDetailsViewTestCase(LoginTestCase):
    def object_create(self):
        data = getattr(self, "{}_data".format(self.object_name))
        data['user'] = self.user.id
        serializer = self.ModelSerializerClass(data = data)
        serializer.is_valid()
        return serializer.save()

    def object_detail_create(self):
        data = getattr(self, "{}_data".format(self.object_name))
        data['api_key'] = api_key
        if self.admin_user_test:
            data['uname'] = phone
        url = getattr(self, "{}_url".format(self.object_name))
        response = self.client.post(url, data = data)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def object_detail_retrieve(self):
        object = self.object_create()
        url = getattr(self, "{}_url".format(self.object_name))
        data = {
            "api_key": api_key,
        }
        if self.admin_user_test:
            data['uname'] = phone
        response = self.client.get(url, data = data)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data'][0]['id'], object.id)

    def object_detail_retrieve_individual(self):
        object = self.object_create()
        url = getattr(self, "{}_url".format(self.object_name))
        data = {
            "api_key": api_key,
            "id": object.id,
        }
        if self.admin_user_test:
            data['uname'] = phone
        response = self.client.get(url, data = data)
        print("Individual: ", response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['id'], object.id)

    def object_detail_update(self):
        object = self.object_create()
        data = {
            "id": object.id,
            "api_key": api_key,
        }
        data.update(**self.update_data)
        if self.admin_user_test:
            data['uname'] = phone
        url = getattr(self, "{}_url".format(self.object_name))
        response = self.client.post(url, data = data)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        object.refresh_from_db()
        serializer = self.ModelSerializerClass(object)
        for key in self.update_data:
            self.assertEqual(serializer.data[key], self.update_data[key])


class PaginateDetailsViewTestCase(LoginTestCase):
    paginate_by = 10
    def get_data(self, num):
        return {}

    def object_list_create(self):
        object_list = []
        cnt = int(self.paginate_by * 1.5)
        for num in range(cnt):
            data = self.get_data(num)
            data['user'] = self.user.id
            serializer = self.ModelSerializerClass(data = data)
            serializer.is_valid()
            obj = serializer.save()
            object_list.append(obj.id)
        
        # This will check that the filtered list
        # returned by api is sorted by id
        object_list.sort()
        return object_list

    def object_detail_paginate(self):
        object_list = self.object_list_create()
        url = getattr(self, "{}_url".format(self.object_name))

        last = -1
        res_object_list = []
        while last:
            data = {"api_key": api_key,}
            if last != -1:
                data['last'] = last
            response = self.client.get(url, data = data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            last = response.json()['last']
            for obj in response.json()['data']:
                res_object_list.append(obj['id'])
            if last:
                self.assertEqual(len(response.json()['data']), self.paginate_by)
                self.assertEqual(int(last), res_object_list[-1])

        self.assertEqual(res_object_list, object_list[::-1])


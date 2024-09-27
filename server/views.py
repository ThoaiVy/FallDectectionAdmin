import json
from datetime import datetime

import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect

from server.enities.patientRequest import PatientRequest
from server.models import Admin

project_id = 'falling-detection-3e200'
collection_register_patient = 'register-patient'
collection_user = 'user'
collection_user_device = 'user-device'
service_account_key_file = './falling-detection-3e200-firebase-adminsdk-bajkv-5e1cc2fe4a.json'


def home(request):
    if 'account' in request.session:
        return render(request, 'index.html')
    return redirect('server:login')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            account = Admin.objects.get(username=username)
            if account.password == password:
                request.session['account'] = account.username
                return redirect('server:home')
            else:
                error_message = 'Tài khoản hoặc mật khẩu không đúng'
                return render(request, 'login.html', {'error_message': error_message})
        except Admin.DoesNotExist:
            error_message = 'Tài khoản hoặc mật khẩu không đúng'
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')


def logout(request):
    if 'account' in request.session:
        del request.session['account']
    return redirect('server:login')


def get_requests(request):
    with open(service_account_key_file) as f:
        service_account_key = json.load(f)
        access_token = service_account_key["private_key"]

    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection_register_patient}?access_token={access_token}"

    response = requests.get(url)
    print(response.json())
    if response.status_code == 200:
        data = response.json()
        patientRequests = []
        for document in data.get('documents', []):
            fields = document.get('fields', {})
            fullName = fields.get('fullName', {}).get('stringValue')
            gender = fields.get('gender', {}).get('integerValue')
            date = fields.get('birthDate', {}).get('timestampValue')
            email = fields.get('email', {}).get('stringValue')
            phone = fields.get('phoneNumber', {}).get('stringValue')

            date_obj = datetime.fromisoformat(date[:-1])
            birthday = date_obj.date()
            patientRequest = PatientRequest(fullName, gender, birthday, email, phone)
            patientRequests.append(patientRequest)
        return render(request, 'request_list.html', {'patientRequests': patientRequests})
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return None


def deleteRequest(request):
    with open(service_account_key_file) as f:
        service_account_key = json.load(f)
        access_token = service_account_key["private_key"]
    email = request.GET.get('email')

    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection_register_patient}/{email}?access_token={access_token}"
    return requests.delete(url)


def cancelRequest(request):
    response = deleteRequest(request)
    if response.status_code == 200:
        return redirect('server:request')
    else:
        return None


def confirmRequest(request):
    with open(service_account_key_file) as f:
        service_account_key = json.load(f)
        access_token = service_account_key["private_key"]

    email = request.GET.get('email')
    deviceID = request.GET.get('deviceID')

    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection_user}?access_token={access_token}"
    response = requests.get(url)

    if response.status_code == 200:
        documents = response.json().get('documents', [])
        device_ids = set()

        for document in documents:
            fields = document.get('fields', {})
            existing_deviceID = fields.get('deviceID', {}).get('stringValue', None)
            if existing_deviceID:
                device_ids.add(existing_deviceID)
        if deviceID in device_ids:
            return JsonResponse({'error': 'Device ID already exists'}, status=400)

        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection_user}/{email}?updateMask.fieldPaths=deviceID&updateMask.fieldPaths=role&access_token={access_token}"

        request_body = {
            "fields": {
                "role": {
                    "integerValue": 1
                },
                "deviceID": {
                    "stringValue": deviceID
                }
            }
        }
        response = requests.patch(url, json=request_body)
        if response.status_code == 200:
            deleteRequest(request)
            return JsonResponse({'success': 'Add patient successfully'},status=200)
        else:
            print(f"Failed to update document. Status code: {response.status_code}")
            return JsonResponse({'error': 'Add patient failed'}, status=400)

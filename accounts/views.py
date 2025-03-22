from django.shortcuts import render
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from .models import *
import face_recognition
from accounts.models import UserImages
import numpy as np

attempts = {}

@csrf_exempt
def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        face_image_data = request.POST.get('face_image')
        
        face_image_data = face_image_data.split(",")[1]
        face_image = ContentFile(base64.b64decode(face_image_data), name=f'{username}_.jpeg')
        
        try:
            user = User.objects.create(username=username)
        except Exception as e:
            return JsonResponse({'status': 'Error', 'message': 'Username Already Registered!'})

        UserImages.objects.create(user=user, face_image=face_image)
        return JsonResponse({'status': 'Success', 'message': 'User Registered Successfully'})
        
    return render(request, 'register.html')


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        face_image_data = request.POST['face_image']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'status': 'Error', 'message': 'Username Doesn’t Exist'})

        face_image_data = face_image_data.split(",")[1]
        uploaded_image = ContentFile(base64.b64decode(face_image_data), name=f'{username}_.jpeg')

        uploaded_face_image = face_recognition.load_image_file(uploaded_image)
        uploaded_face_encoding = face_recognition.face_encodings(uploaded_face_image)

        if not uploaded_face_encoding:
            return JsonResponse({'status': 'Error', 'message': 'No face detected in the image, try again'})

        uploaded_face_encoding = uploaded_face_encoding[0]

        user_image = UserImages.objects.filter(user=user).last()
        if user_image is None:
            return JsonResponse({'status': 'Error', 'message': 'No face image found for this user'})

        stored_face_image = face_recognition.load_image_file(user_image.face_image.path)
        stored_face_encoding = face_recognition.face_encodings(stored_face_image)

        if not stored_face_encoding:
            return JsonResponse({'status': 'Error', 'message': 'No face detected in the stored image'})

        stored_face_encoding = stored_face_encoding[0]

        match = face_recognition.compare_faces([stored_face_encoding], uploaded_face_encoding)

        if np.any(match):
            if username in attempts:
                attempts[username] = 0
            return JsonResponse({'status': 'Success', 'message': 'Logged in Successfully'})

        if username not in attempts:
            attempts[username] = 0
        attempts[username] += 1

        if attempts[username] >= 3:
            return JsonResponse({'status': 'Error', 'message': 'Too many failed attempts. Please try again later.'})

        return JsonResponse({'status': 'Error', 'message': 'Picture Doesnt Match, Try again'})

    return render(request, 'login.html')

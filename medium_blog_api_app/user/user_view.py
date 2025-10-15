from django.forms import ValidationError
from medium_blog_api_app.models import * 
from medium_blog_api_app.serializers import *
from rest_framework.response import Response
from tokenize import TokenError
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from medium_blog_api_app.utils import *

# Register user class using serializer
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    enter_username =  request.data.get('username')
    enter_fullname =  request.data.get('fullname')
    enter_email = request.data.get('email')
    enter_password = request.data.get('password')
    enter_contact_number = request.data.get('contact_number')
    enter_bio = request.data.get('bio')
    enter_gender = request.data.get('gender')
    enter_profile_pic = request.FILES.get('profile_pic')
    if enter_profile_pic:
        try:
            validate_image(enter_profile_pic)
        except ValidationError as e:
            return Response({"status":"fail","message":str(e)}, status=status.HTTP_400_BAD_REQUEST)

    if not request.data.get("username") or not request.data.get("email") or not request.data.get("password") or not request.data.get("confirm_password"):
        return Response({"status":"fail","message":"username, email, password required"}, status=status.HTTP_400_BAD_REQUEST)

    raw_password = request.data.get("password")
    enter_confirm_password = request.data.get("confirm_password")

    if raw_password != enter_confirm_password:
        return Response({"status":"fail","message":"Password and confirm password do not match"}, status=status.HTTP_400_BAD_REQUEST)

    enter_password = make_password(raw_password)

    if User.objects.filter(username=request.data["username"]).exists():
        return Response({"status":"fail","message":"Username already exist, try some diffrent username."}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=request.data["email"]).exists():
        return Response({"status":"fail","message":f"Email  with Email ID: {enter_email} already registered"}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(contact_number = request.data["contact_number"]).exists():
        return Response({"status":"fail", "message":f"user with contact number: {enter_contact_number} already registered"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            user = User.objects.create(
                username = enter_username,
                full_name = enter_fullname,
                email = enter_email,
                password = enter_password,
                contact_number = enter_contact_number,
                bio = enter_bio,
                gender = enter_gender,
                profile_pic = enter_profile_pic,
            )
            user.save()
            serializer = UserSerializer(user, context={'request': request})
            return Response({"status":"success",'message': 'User registered successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
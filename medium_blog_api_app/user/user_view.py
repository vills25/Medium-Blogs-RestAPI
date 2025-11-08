from django.forms import ValidationError
from loguru import logger
from medium_blog_api_app.authentication.custom_jwt_auth import IsAuthenticatedCustom
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

    logger.info("Registering a new user")
    """
    Register a new user
    Parameters:
    username: str
    fullname: str
    email: str
    password: str
    confirm_password: str
    contact_number: str
    bio: str
    gender: str
    profile_pic: file

    Response:
    {
        "status": "success",
        "message": "User registered successfully",
        "data": {
            "user_id": "int",
            "username": "string",
            "email": "string",
            "full_name": "string",
            "contact_number": "string",
            "bio": "string",
            "profile_pic": "string",
            "followers_count": "int"
        }
    }
    """
    enter_username =  request.data.get('username')
    enter_fullname =  request.data.get('fullname')
    enter_email = request.data.get('email')
    enter_password = request.data.get('password')
    enter_contact_number = request.data.get('contact_number')
    enter_bio = request.data.get('bio')
    enter_gender = request.data.get('gender')
    enter_profile_pic = request.FILES.get('profile_pic')

    logger.debug(f"Registration data - Username: {enter_username}, Email: {enter_email}, Contact: {enter_contact_number}")

    if enter_profile_pic:
        try:
            validate_image(enter_profile_pic)
            logger.debug("Profile picture validation passed")
        except ValidationError as e:
            logger.warning(f"Profile picture validation failed: {str(e)}")
            return Response({"status":"fail","message":str(e)}, status=status.HTTP_400_BAD_REQUEST)

    if not request.data.get("username") or not request.data.get("email") or not request.data.get("password") or not request.data.get("confirm_password"):
        logger.warning("Registration failed - Missing required fields")
        return Response({"status":"fail","message":"username, email, password required"}, status=status.HTTP_400_BAD_REQUEST)

    raw_password = request.data.get("password")
    enter_confirm_password = request.data.get("confirm_password")

    if raw_password != enter_confirm_password:
        logger.warning("Registration failed - Password mismatch")
        return Response({"status":"fail","message":"Password and confirm password do not match"}, status=status.HTTP_400_BAD_REQUEST)

    enter_password = make_password(raw_password)

    if User.objects.filter(username=request.data["username"]).exists():
        logger.warning(f"Registration failed - Username already exists: {enter_username}")
        return Response({"status":"fail","message":"Username already exist, try some diffrent username."}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=request.data["email"]).exists():
        logger.warning(f"Registration failed - Email already registered: {enter_email}")
        return Response({"status":"fail","message":f"Email  with Email ID: {enter_email} already registered"}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(contact_number = request.data["contact_number"]).exists():
        logger.warning(f"Registration failed - Contact number already registered: {enter_contact_number}")
        return Response({"status":"fail", "message":f"user with contact number: {enter_contact_number} already registered"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            logger.debug("Starting user creation transaction")
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
            logger.success(f"User registered successfully: {enter_username} (ID: {user.user_id})")
            serializer = UserSerializer(user, context={'request': request})
            return Response({"status":"success",'message': 'User registered successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"User registration error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Login user
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login user using username, email or phone_number and password.
    Parameters:
    username/email/phone_number: str
    password: str
    """
    username = request.data.get("username/email/phone_number")
    password = request.data.get("password")

    try:
        logger.info(f"Login attempt for: {username}")
        user = User.objects.filter(Q(username=username) | Q(email=username) | Q(contact_number=username)).first()

        if not username or not password:
            return Response({"status":"fail","message":"please enter username and password"}, status=status.HTTP_400_BAD_REQUEST)

        if not user:
            logger.warning(f"Login failed - User not found: {username}")
            return Response({"status":"fail","message":"User not found"}, status=status.HTTP_404_NOT_FOUND)

        if not check_password(password, user.password):
            logger.warning(f"Login failed - Invalid password for user: {username}")
            return Response({"status":"fail","message":"Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)

        logger.success(f"Login successful for user: {user.username}")
        user_data = {"username": user.username, "email": user.email, "full_name": user.full_name}
        
        if user:
            refresh = RefreshToken()
            refresh['user_id'] = user.user_id
            refresh['username'] = user.username
            logger.debug(f"JWT tokens generated for user: {user.username}")

        return Response({"status": "success","message": "Login successful","data":{"User": user_data,"access_token": str(refresh.access_token)}}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.error(f"Login failed - User does not exist: {username}")
        return Response({"status":"fail","message":"User not found or account is deactivated"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

## logout User
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def logout_user(request):
    """
    Logout user
    This API is used to logout user from the system and add the access token to the blacklist.
    Parameters:
    - request: The request object
    
    Response:
   {
    "status": "success",
    "message": "Logout successful"
  }
    """
    logger.info(f"Logout attempt for user: {request.user.username}")
    try:
        access_token = request.auth

        if isinstance(access_token, bytes):
            access_token = access_token.decode("utf-8")

        with transaction.atomic():
            TokenBlacklistLogout.objects.create(
                user=request.user,
                token=str(access_token),
                is_expired=True,
                expire_datetime=timezone.now()
            )
        logger.success(f"Logout successful for user: {request.user.username}")
        return Response({"status":"success","message": "Logout successful"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Logout error for user {request.user.username}: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
## edit profile
@api_view(['PUT'])
@permission_classes([IsAuthenticatedCustom])
def edit_profile(request):
    """
    Edit profile
    This API is used to edit user profile from the system.
    Parameters:
    - request: The request object
    
    Request Body:
    {
        "username": "string",
        "email": "string",
        "full_name": "string",
        "contact_number": "string",
        "bio": "string",
        "gender": "string",
        "profile_pic": "file",
        "remove_profile_pic": "boolean"
    }

    Response:
    {
        "status": "success",
        "message": "Profile updated successfully",
        "data": {
            "user_id": "int",
            "username": "string",
            "email": "string",
            "full_name": "string",
            "contact_number": "string",
            "profile_pic": "string",
            "bio": "string",
            "gender": "string"
        }
    }
    """

    logger.info(f" Profile edit attempt for user: {request.user.username}")
    try:
        user = request.user

        get_username = request.data.get('username')
        get_email = request.data.get('email')
        get_full_name = request.data.get('full_name')
        get_contact_number = request.data.get('contact_number')
        get_bio = request.data.get('bio')
        get_gender = request.data.get('gender')
        get_profile_pic = request.FILES.get('profile_pic')
        get_remove_profile_pic = request.data.get('remove_profile_pic')

        logger.debug(f"Profile update data - Username: {get_username}, Email: {get_email}, Full Name: {get_full_name}")

        with transaction.atomic():

            if request.user.user_id != user.user_id and not request.user.is_superuser:
                    logger.warning(f" Profile edit denied - User {request.user.username} trying to edit other user's profile")
                    return Response({"status":"fail", "message": "you can not update others profile"}, status=status.HTTP_403_FORBIDDEN)

            # Validate and assign new profile picture
            if get_profile_pic:
                try:
                    validate_image(get_profile_pic)
                    user.profile_pic = get_profile_pic
                    logger.debug("Profile picture updated")
                except ValidationError as e:
                    logger.warning(f"Profile picture validation failed: {str(e)}")
                    return Response({"status": "fail", "message": str(e)},status=status.HTTP_400_BAD_REQUEST)

            if get_remove_profile_pic in ['true', 'True']:
                if user.profile_pic:
                    user.profile_pic.delete(save=False)
                    user.profile_pic = None
                    logger.debug("Profile picture removed")

            if get_username:
                if User.objects.filter(username=get_username).exists():
                    logger.warning(f"Profile update failed - Username already exists: {get_username}")
                    return Response({"status":"fail","message":"Username already exist, try some diffrent username."}, status=status.HTTP_400_BAD_REQUEST)
                user.username = get_username

            if get_email:
                if User.objects.filter(email=get_email).exists():
                    logger.warning(f"Profile update failed - Email already registered: {get_email}")
                    return Response({"status":"fail", "message":f"user with email: {get_email} already registered"}, status=status.HTTP_400_BAD_REQUEST)
                user.email = get_email

            if get_contact_number:
                if User.objects.filter(contact_number = get_contact_number).exists():
                    logger.warning(f"Profile update failed - Contact number already registered: {get_contact_number}")
                    return Response({"status":"fail", "message":f"user with contact number: {get_contact_number} already registered"}, status=status.HTTP_400_BAD_REQUEST)
                user.contact_number = get_contact_number

            if get_full_name:
                user.full_name = get_full_name
                logger.debug(f"Full name updated to: {get_full_name}")

            if get_bio:
                user.bio = get_bio
                logger.debug("Bio updated")

            if get_gender:
                user.gender = get_gender
                logger.debug(f"Gender updated to: {get_gender}")

            user.updated_at = timezone.now()
            user.updated_by = request.user
            user.save()

            logger.success(f"Profile updated successfully for user: {user.username}")
            serializer = UserShortDetailSerializer(user, context={'request': request})
            return Response({"status":"success","message": "Profile updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Profile edit error for user {request.user.username}: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
## Delete/Deactivate profile
@api_view(['DELETE'])
@permission_classes([IsAuthenticatedCustom])
def delete_profile(request):
    """
    Delete profile
    This API is used to delete user profile from the system.
    Parameters:
    - request: The request object
    
    Request Body:
    {
        "user_id": "int"
    }

    Response:
    {
        "status": "success",
        "message": "Profile deleted successfully"
    }
    """
    logger.info(f" Profile deletion attempt by user: {request.user.username}")
    user = request.data

    if not request.user.is_superuser and request.user.user_id != user.user_id:
        logger.warning(f" Profile deletion denied - User {request.user.username} trying to delete other user's profile")
        return Response({"status":"fail", "message": "you can not delete others profile"}, status=status.HTTP_403_FORBIDDEN)

    try:
        with transaction.atomic():
            user = User.objects.get(user_id=user.user_id)
            user.delete()
            user.save()
            logger.success(f" Profile deleted successfully: {user.username}")
            message = "Profile deleted successfully"
            return Response({"status":"success","message": message}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f" Profile deletion error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

## Deactivate User profile/account
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def deactivate_profile(request):
    """
    Deactivate User profile/account
    This API is used to deactivate user profile/account from the system.
    Parameters:
    - request: The request object
    Request Body:
    {
        "deactivate": "boolean"
    }
    Response:
    {
        "status": "success",
        "message": "Profile deactivated successfully"
    }
    """
    logger.info(f"Profile deactivation attempt by user: {request.user.username}")
    user = request.user
    get_deactivate_request = request.data.get('deactivate')

    if request.user.user_id != user.user_id:
        logger.warning(f" Profile deactivation denied - User {request.user.username} trying to deactivate other user")
        return Response({"status":"fail", "message": "you can not deactivate others profile"}, status=status.HTTP_403_FORBIDDEN)

    try:
        with transaction.atomic():
            user = User.objects.get(user_id=user.user_id)
            if get_deactivate_request in ['true', 'True']:     
                user.is_active = False
                user.is_member = False
                TokenBlacklistLogout.objects.create(user=request.user,token=str(request.auth.token),is_expired=True,expire_datetime=timezone.now())
                user.save()
                logger.success(f" Profile deactivated successfully: {user.username}")
                return Response({"status":"success","message": "Profile deactivated successfully"}, status=status.HTTP_200_OK)
            else:
                logger.warning(" Deactivation request not set to true")
                return Response({"status":"fail","message": "Deactivation not confirmed"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f" Profile deactivation error for user {request.user.username}: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

## Change password
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def change_password(request):
    """
    Change user password
    This API is used to change user password from the system.
    Parameters:
    - request: The request object
    Request Body:
    {
        "old_password": "string",
        "new_password": "string",
        "confirm_password": "string"
    }
    Response:
    {
        "status": "success",
        "message": "Password changed successfully"
    }
    """
    logger.info(f" Password change attempt for user: {request.user.username}")
    try:
        user = request.user

        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not old_password or not new_password or not confirm_password:
            logger.warning(" Password change failed - Missing required fields")
            return Response({"status":"fail","message":"All password fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(old_password, user.password):
            logger.warning(f" Password change failed - Invalid old password for user: {user.username}")
            return Response({"status":"fail","message":"Invalid old password"}, status=status.HTTP_401_UNAUTHORIZED)

        if new_password != confirm_password:
            logger.warning(" Password change failed - New password and confirm password mismatch")
            return Response({"status":"fail","message":"New password and confirm password do not match"}, status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(new_password)
        user.save()

        logger.success(f" Password changed successfully for user: {user.username}")
        return Response({"status":"success","message":"Password changed successfully"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f" Password change error for user {request.user.username}: {str(e)}")  
        return Response({"status":"error","message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

## Forgot password
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    Forgot password API
    This API is used to send OTP to the email to reset the password.
    Parameters:
    - request: The request object
    
    Request Body:
    {
        "email": "string"
    }
    
    Response:
    {
        "status": "success",
        "message": "OTP sent to email id: <email>"
    }
    """
    logger.info("Forgot password request")
    email = request.data.get("email")

    if not email:
        logger.warning("Forgot password failed - Email not provided")
        return Response({"status":"fail","message":"email required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(email=email)
        otp = generate_otp()
        request.session["reset_email"] = email
        request.session["reset_otp"] = otp
        request.session["reset_time"] = str(timezone.now())
        logger.debug(f"OTP generated to email id: {email}")
        send_otp_email(email, otp)
        logger.success(f"OTP sent to email id: {email}")
        return Response({"status":"success","message":f"OTP sent to email id: {email}"}, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        logger.warning(f"Forgot password failed - User not found with email: {email}")
        return Response({"status":"fail","message":"User not found"}, status=status.HTTP_404_NOT_FOUND)
    
## Reset Password
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Reset password API
    This API is used to reset the password of the user.
    Parameters:
    - request: The request object
    
    Request Body:
    {
        "email": "string",
        "otp": "string",
        "new_password": "string",
        "confirm_new_password": "string"
    }
    
    Response:
    {
        "status": "success",
        "message": "Password changed successfully"
    }
    """
    logger.info("Reset password attempt")
    email = request.data.get("email")
    otp = request.data.get("otp")
    raw_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_new_password")
    new_password = check_password(raw_password, confirm_password)

    if not email or not otp or not raw_password or not confirm_password:
            logger.warning("Reset password failed - Missing required fields")
            return Response({"status":"fail","message":"email, otp, new_password required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)

        if request.session.get("reset_email") != email or request.session.get("reset_otp") != otp:
            logger.warning(f"Reset password failed - Invalid OTP for email: {email}")
            return Response({"status":"fail","message":"Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if raw_password != confirm_password:
            logger.warning("Reset password failed - New password and confirm password mismatch")
            return Response({"status":"fail","message":"Password and confirm password do not match"}, status= status.HTTP_400_BAD_REQUEST)

        user.password = make_password(raw_password)
        user.save()

        logger.success(f"Password changed successfully for user: {user.username}")
        return Response({"status":"success","message":"Password changed successfully"}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.warning(f"Reset password failed - User not found with email: {email}")
        return Response({"status": "fail", "message":"User not found"}, status= status.HTTP_404_NOT_FOUND)

    except Exception as e:  
        logger.error(f"Reset password error for user: {user.username}: {str(e)}")  
        return Response({"status":"error","message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

## Follow user
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def follow_user(request):
    """
    Follow/Unfollow a user
    Parameters:
    user_id: int
    mark_as_following: bool
    Response:
    {
        "status": "success",
        "message": "You are now following <username>"
    }
    """
    logger.info(f"Follow user attempt by user: {request.user.username}")
    follower = request.user
    target_user_id = request.data.get('user_id')
    mark_as_following = request.data.get('mark_as_following')

    if not target_user_id:
        logger.warning(f"Follow user failed - user_id is required")
        return Response({"status": "error", "message": "user_id is required"},status=status.HTTP_400_BAD_REQUEST)

    if follower.user_id == target_user_id:
        logger.warning(f"Follow user failed - You cannot follow yourself")
        return Response({"status": "fail", "message": "You cannot follow yourself"},status=status.HTTP_400_BAD_REQUEST)

    try:
        target_user = User.objects.get(user_id = target_user_id)

        if target_user in follower.following_users.all():
            logger.warning(f"Follow user failed - Already following this user: {target_user.username}")
            return Response({"status": "fail", "message": "Already following this user"},status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if mark_as_following == 'true' or mark_as_following == 'True':
                follower.following_users.add(target_user)
                target_user.followers_count += 1
                target_user.save(update_fields=['followers_count'])
                logger.success(f"user:{follower.username} are now following {target_user.username}")

        return Response({"status": "success", "message": f"You are now following {target_user.username}"},status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.warning(f"Follow user failed - User not found with user_id: {target_user_id}")
        return Response({"status": "error", "message": "User not found"},status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Follow user error for user: {follower.username}: {str(e)}")
        return Response({"status": "error", "message": str(e)},status=status.HTTP_400_BAD_REQUEST)

## Unfollow user
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def unfollow_user(request):
    """
    Unfollow a user
    Parameters:
    user_id: int
    mark_as_unfollow: bool
    Response:
    {
        "status": "success",
        "message": "You unfollowed <username>"
    }
    """
    logger.info(f"Unfollow user attempt by user: {request.user.username}")
    follower = request.user
    target_user_id = request.data.get('user_id')
    mark_as_unfollow = request.data.get('mark_as_unfollow')

    if not target_user_id:
        logger.warning(f"Unfollow user failed - user_id is required")
        return Response({"status": "error", "message": "user_id is required"},status=status.HTTP_400_BAD_REQUEST)

    if follower.user_id == target_user_id:
        logger.warning(f"Unfollow user failed - You cannot unfollow yourself")
        return Response({"status": "fail", "message": "You cannot follow yourself"},status=status.HTTP_400_BAD_REQUEST)

    try:
        target_user = User.objects.get(user_id = target_user_id)

        if target_user not in follower.following_users.all():
            logger.warning(f"Unfollow user failed - You are not following this user: {target_user.username}")
            return Response({"status": "fail", "message": "You are not following this user"},status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if mark_as_unfollow == 'true' or mark_as_unfollow == 'True':
                follower.following_users.remove(target_user)
                target_user.followers_count -= 1
                target_user.save(update_fields=['followers_count'])
                logger.success(f"user:{follower.username} unfollowed {target_user.username}")
        return Response({"status": "success", "message": f"You unfollowed {target_user.username}"},status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.warning(f"Unfollow user failed - User not found with user_id: {target_user_id}")
        return Response({"status": "error", "message": "User not found"},status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Unfollow user error for user: {follower.username}: {str(e)}")
        return Response({"status": "error", "message": str(e)},status=status.HTTP_400_BAD_REQUEST)

## View my profile
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def view_my_profile(request):
    """
    View my profile
    Parameters:
    None
    Response:
    {
        "status": "success",
        "message": "Profile fetched successfully",
        "data": {
            "user_id": "int",
            "username": "string",
            "email": "string",
            "full_name": "string",
            "contact_number": "string",
            "bio": "string",
            "profile_pic": "string",
            "followers_count": "int"
        }
    }
    """
    logger.info(f"View my profile attempt by user: {request.user.username}")
    try:
        user = User.objects.get(user_id=request.user.user_id)
        serializer = UserSerializer(user, context={'request': request})

        logger.success(f"View my profile success for user: {request.user.username}")
        return Response({"status":"success","message":"Profile fetched successfully","data":serializer.data}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.warning(f"View my profile failed - User not found with user_id: {request.user.user_id}")
        return Response({"status":"fail","message":"User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"View my profile error for user: {request.user.username}: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
## view other user profile
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def view_other_user_profile(request):

    """
    View other user profile
    Parameters:
    - user_id: int (user_id of the user whose profile is to be viewed)
    """

    get_userid = request.data.get('user_id')
    logger.info(f"View other user profile attempt by user: {request.user.username}")

    if not get_userid:
        logger.warning(f"View other user profile failed - user_id is required")
        return Response({"status":"error","message":"user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(user_id=get_userid)
        serializer = UserProfileSerializer(user, context={'request': request})

        logger.success(f"View other user profile success for user: {request.user.username}")
        return Response({"status":"success","message":"Profile fetched successfully","data":serializer.data}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.warning(f"View other user profile failed - User not found with user_id: {get_userid}")
        return Response({"status":"fail","message":"User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"View other user profile error for user: {request.user.username}: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
## view my following lists user/publications..
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def view_my_following_list(request):
    """
    View my following lists user/publications.
    Parameters:
    None
    Response:
    {
        "status": "success",
        "message": "Following list fetched",
        "results": {
            "users": [
                {
                    "user_id": "int",
                    "username": "string",
                    "full_name": "string",
                    "profile_pic": "string"
                }
            ],
            "publications": [
                {
                    "publication_id": "int",
                    "publication_title": "string",
                    "logo_image": "string",
                    "owner": "string"
                }
            ]
        }
    }
    """
    logger.info(f"View my following list attempt by user: {request.user.username}")
    try:
        user = request.user

        following_users = user.following_users.all()
        users_data = [
            {
                "user_id": u.user_id,
                "username": u.username,
                "full_name": u.full_name,
                "profile_pic": request.build_absolute_uri(u.profile_pic.url) if u.profile_pic else None
            }
            for u in following_users
        ]

        following_publications = Publication.objects.filter(followers=user)
        publications_data = [
            {
                "publication_id": p.publication_id,
                "publication_title": p.publication_title,
                "logo_image": request.build_absolute_uri(p.logo_image.url) if p.logo_image else None,
                "owner": p.owner.username
            }
            for p in following_publications
        ]

        logger.success(f"View my following list success for user: {request.user.username}")
        return Response({"status": "success","message": "Following list fetched","results": {"users": users_data,"publications": publications_data}},status=status.HTTP_200_OK)
                                
    except Exception as e:
        logger.error(f"View my following list error for user: {request.user.username}: {str(e)}")
        return Response({"status": "error", "message": str(e)},status=status.HTTP_400_BAD_REQUEST)
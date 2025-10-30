from rest_framework.permissions import BasePermission
from tokenize import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from medium_blog_api_app.models import TokenBlacklistLogout, User
from rest_framework_simplejwt.tokens import RefreshToken

# custome JWT configure
class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)

        except TokenError as e:
            raise exceptions.AuthenticationFailed(str(e))

    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
            user = User.objects.get(user_id=user_id)
            return user
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found', code='user_not_found')
        except KeyError:
            raise exceptions.AuthenticationFailed('Invalid token')

# Utility function to get tokens for user
def get_tokens_for_user(user):
    
    refresh = RefreshToken.for_user(user)
    
    # Add custom claims
    refresh['user_id'] = user.user_id
    refresh['username'] = user.username
    refresh['role'] = user.role
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# Function to validate if token is blacklisted
def validate_token_not_blacklisted(request):
    validated_token = request.auth
    if not validated_token:
        raise exceptions.AuthenticationFailed("No token found.")

    if isinstance(validated_token, bytes):
        validated_token = validated_token.decode("utf-8")

    if TokenBlacklistLogout.objects.filter(
        user=request.user,
        token=str(validated_token),
        is_expired=True
    ).exists():
        raise exceptions.AuthenticationFailed("Token blacklisted. Please login again.")

# Custom Permission Classes
class IsAuthenticatedCustom(BasePermission):
    """
    Custom permission class that works with your User model
    """
    def has_permission(self, request, view):
        if not (request.user and hasattr(request.user, 'user_id')):
            return False

        validated_token = request.auth
        if not validated_token:
            raise exceptions.AuthenticationFailed("Access token missing.")
        
        if isinstance(validated_token, bytes):
            validated_token = validated_token.decode("utf-8")

        is_blacklisted = TokenBlacklistLogout.objects.filter(
            user=request.user,
            token=str(validated_token),
            is_expired=True
        ).exists()

        if is_blacklisted:
            raise exceptions.AuthenticationFailed("This access token has been blacklisted. Please log in again.")

        return True

class IsAdminCustom(BasePermission):
    """
    Allows access only to admin users.
    """
    # def has_permission(self, request, view):
    #         validate_token_not_blacklisted(request)
            
    #         if not (request.user and hasattr(request.user, 'user_id') and hasattr(request.user, 'role')):
    #             return False
    #         if request.user.role != "admin":
    #             return False

    #         return True

    def has_permission(self, request, view):
        # token check
        validate_token_not_blacklisted(request)

        user = request.user
        if not user or not hasattr(user, 'user_id'):
            return False

        if not getattr(user, 'is_admin', False):
            return False

        return True


class IsMemberUser(BasePermission):
    """
    Permission class to allow access only to member users
    for member-only content.
    """
    message = "You must be a member to access this content."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_member

    def has_object_permission(self, request, view, obj):
        # Check object level: member-only article
        if hasattr(obj, 'is_member_only') and obj.is_member_only:
            return request.user.is_authenticated and request.user.is_member
        return True

from rest_framework.permissions import BasePermission
from tokenize import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from medium_blog_api_app.models import TokenBlacklistLogout, User
from rest_framework_simplejwt.tokens import RefreshToken
from loguru import logger

# Custom JWT configure
class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        
        header = self.get_header(request)
        if header is None:
            logger.warning("No authorization header found")
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            logger.warning("No token found in authorization header")
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            logger.info(f"User authenticated: {user.username} (ID: {user.user_id})")
            return (user, validated_token)

        except TokenError as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise exceptions.AuthenticationFailed(str(e))

    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
            user = User.objects.get(user_id=user_id)
            logger.debug(f"User retrieved from token: {user.username}")
            return user
        except User.DoesNotExist:
            logger.error(f"User not found for ID: {user_id}")
            raise exceptions.AuthenticationFailed('User not found', code='user_not_found')
        except KeyError:
            logger.error("Invalid token - missing user_id")
            raise exceptions.AuthenticationFailed('Invalid token')

# Utility function to get tokens for user
def get_tokens_for_user(user):
    logger.info(f"Generating tokens for user: {user.username}")
    
    refresh = RefreshToken.for_user(user)
    
    # Add custom claims
    refresh['user_id'] = user.user_id
    refresh['username'] = user.username
    refresh['role'] = user.role
    
    logger.success(f"Tokens generated successfully for user: {user.username}")
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# Function to validate if token is blacklisted
def validate_token_not_blacklisted(request):
    validated_token = request.auth
    if not validated_token:
        logger.warning("No token found in request")
        raise exceptions.AuthenticationFailed("No token found.")

    if isinstance(validated_token, bytes):
        validated_token = validated_token.decode("utf-8")

    is_blacklisted = TokenBlacklistLogout.objects.filter(
        user=request.user,
        token=str(validated_token),
        is_expired=True
    ).exists()

    if is_blacklisted:
        logger.warning(f"Blacklisted token used by user: {request.user.username}")
        raise exceptions.AuthenticationFailed("Token blacklisted. Please login again.")
    
    logger.debug(f"Token validation passed for user: {request.user.username}")

# Custom Permission Classes
class IsAuthenticatedCustom(BasePermission):
    """
    Custom permission class that works with your User model
    """
    def has_permission(self, request, view):
        
        if not (request.user and hasattr(request.user, 'user_id')):
            logger.warning("Permission denied - No user or user_id")
            return False

        validated_token = request.auth
        if not validated_token:
            logger.warning("Permission denied - No access token")
            raise exceptions.AuthenticationFailed("Access token missing.")
        
        if isinstance(validated_token, bytes):
            validated_token = validated_token.decode("utf-8")

        is_blacklisted = TokenBlacklistLogout.objects.filter(
            user=request.user,
            token=str(validated_token),
            is_expired=True
        ).exists()

        if is_blacklisted:
            logger.warning(f"Permission denied - Blacklisted token for user: {request.user.username}")
            raise exceptions.AuthenticationFailed("This access token has been blacklisted. Please log in again.")

        logger.info(f"IsAuthenticatedCustom permission granted for user: {request.user.username}")
        return True

class IsAdminCustom(BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        
        # token check
        validate_token_not_blacklisted(request)

        user = request.user
        if not user or not hasattr(user, 'user_id'):
            logger.warning("Admin permission denied - No user or user_id")
            return False

        if not getattr(user, 'is_admin', False):
            logger.warning(f"Admin permission denied - User {user.username} is not admin")
            return False

        logger.info(f"IsAdminCustom permission granted for admin: {user.username}")
        return True

class IsMemberUser(BasePermission):
    """
    Permission class to allow access only to member users
    for member-only content.
    """
    message = "You must be a member to access this content."

    def has_permission(self, request, view):
        
        is_member = request.user and request.user.is_authenticated and request.user.is_member
        
        if not is_member:
            logger.warning(f"Member permission denied - User {getattr(request.user, 'username', 'Unknown')} is not a member")
        
        logger.info(f"IsMemberUser permission granted for member: {request.user.username}")
        return is_member

    def has_object_permission(self, request, view, obj):
        
        # Check object level: member-only article
        if hasattr(obj, 'is_member_only') and obj.is_member_only:
            is_member = request.user.is_authenticated and request.user.is_member
            if not is_member:
                logger.warning(f"Object member permission denied for article: {getattr(obj, 'article_title', 'Unknown')}")
            return is_member
        
        logger.debug("Object member permission granted (not member-only content)")
        return True
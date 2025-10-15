from medium_blog_api_app.models import *
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'contact_number', 'bio', 'profile_pic', 'followers', 'is_writer', 'is_following', 'is_member', 'is_active', 'is_blocked', 'is_muted', 'created_at', 'updated_at']


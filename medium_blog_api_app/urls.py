from django.urls import path, include
from medium_blog_api_app.user.user_view import register_user

urlpatterns = [
    path('register/', register_user),

]
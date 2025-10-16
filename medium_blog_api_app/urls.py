from django.urls import path, include
from medium_blog_api_app.user.user_view import *

urlpatterns = [
    path('register/', register_user),
    path('login/', login_user),
    path('logout/', logout_user),
    path('edit-profile/', edit_profile),
    path('delete-profile/', delete_profile),
    path('deactivate-profile/', deactivate_profile),
    path('change-password/', change_password),
    path('forgot-password/', forgot_password),
    path('reset-password/', reset_password),

]
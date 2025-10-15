from django.contrib import admin
from .models import *

admin.site.site_header = "Medium Blog Admin Corner"
admin.site.site_title = "Medium Blog"
admin.site.index_title = "Medium Blog admin" 

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'email','is_active')
    search_fields = ['username', 'email', 'full_name']

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_at', 'updated_at')

class PublicationAdmin(admin.ModelAdmin):
    list_display = ('publication_title', 'owner', 'created_at')

class TokenBlacklistLogoutAdmin(admin.ModelAdmin):
    list_display = ('user','is_expired','expire_datetime','token')

admin.site.register(User, UserAdmin)
admin.site.register(Article,ArticleAdmin)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(TokenBlacklistLogout,TokenBlacklistLogoutAdmin)
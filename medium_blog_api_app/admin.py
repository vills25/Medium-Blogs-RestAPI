from django.contrib import admin
from .models import *

admin.site.site_header = "Medium Blog Admin Corner"
admin.site.site_title = "Medium Blog"
admin.site.index_title = "Medium Blog admin" 

class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id','username', 'full_name', 'email','is_active')
    search_fields = ['user_id','username', 'email', 'full_name']

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('article_title', 'author', 'publication','article_id','is_member_only','published_by','published_at', 'is_reported','updated_at')

class PublicationAdmin(admin.ModelAdmin):
    list_display = ('publication_title', 'owner', 'created_at')

class TokenBlacklistLogoutAdmin(admin.ModelAdmin):
    list_display = ('user','is_expired','expire_datetime','token')

class TopicAdmin(admin.ModelAdmin):
    list_display = ('topic_id', 'topic_header_1', 'total_stories', 'total_followers')

class ArticlePublicationTopicAdmin(admin.ModelAdmin):
    list_display = ('apt_id', 'topic', 'article', 'publication')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment_id', 'user', 'article', 'created_at', 'updated_at')

class ReadingListAdmin(admin.ModelAdmin):
    list_display = ('reading_list_id','user', 'article', 'visibility','created_at', 'updated_at')

class StaffPicsAdmin(admin.ModelAdmin):
    list_display = ('staff_pic_id', 'article', 'topic', 'publications', 'total_stories', 'total_saves', 'created_at', 'updated_at')

admin.site.register(User, UserAdmin)
admin.site.register(Article,ArticleAdmin)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(TokenBlacklistLogout,TokenBlacklistLogoutAdmin)
admin.site.register(Topics, TopicAdmin)
admin.site.register(ArticlePublicationTopic, ArticlePublicationTopicAdmin)
admin.site.register(StaffPics, StaffPicsAdmin)
admin.site.register(ReadingList, ReadingListAdmin)
admin.site.register(Comment,CommentAdmin)
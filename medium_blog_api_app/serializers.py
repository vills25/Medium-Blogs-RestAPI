from medium_blog_api_app.models import *
from rest_framework import serializers

################### USER ######################
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id','username','full_name','email','profile_pic','contact_number','bio','gender','is_writer','is_member','is_active','is_following','following_users',
                'is_following_publications','followers_count','created_at','updated_at']

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'username', 'full_name', 'profile_pic', 'bio','followers_count', 'is_writer', 'is_member']

class UserShortDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'contact_number', 'bio', 'profile_pic','is_writer', 'is_member']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'full_name', 'email', 'contact_number', 'bio', 'profile_pic','gender', 'followers_count', 'is_writer']

################### PUBLICATION ######################
class PublicationSerializer(serializers.ModelSerializer):
    owner = UserShortSerializer(read_only=True)
    class Meta:
        model = Publication
        fields = '__all__'

################### ARTICLE ######################
class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['article_id', 'author', 'article_title','article_subtitle','article_content', 'article_category','url', 'image', 'video', 'code_block','read_time', 
                'publication', 'is_member_only', 'published_at', 'published_by', 'clap_count', 'comment_count', 'is_saved', 'is_reported']

class ArticleDetailSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    publication = PublicationSerializer(read_only=True)
    class Meta:
        model = Article
        fields = ['article_id','article_title','article_subtitle','author','publication','read_time','clap_count','comment_count','published_at','is_member_only']

    def get_author(self, obj):
        return obj.author.full_name if obj.author else None

class ArticleListSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="user.full_name", read_only=True)
    publication = PublicationSerializer(read_only=True)
    class Meta:
        model = Article
        fields = ['article_id','article_title','article_subtitle','article_content','author','publication','read_time','clap_count','comment_count','published_at','is_member_only']

class ArticleFeedSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    publication = serializers.CharField(source='publication.publication_title', read_only=True)
    original_author_name = serializers.SerializerMethodField()
    is_shared = serializers.SerializerMethodField()
    shared_from = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'article_id', 'article_title', 'article_subtitle', 'author',
            'publication', 'is_member_only', 'article_content',
            'published_at', 'image', 'url', 'read_time', 'clap_count', 'comment_count',
            'original_author_name', 'is_shared', 'shared_from', 'share_count'
        ]

    def get_original_author_name(self, obj):
        return obj.shared_from.author.username if obj.shared_from else None

    def get_is_shared(self, obj):
        return True if obj.shared_from else False

    def get_shared_from(self, obj):
        return obj.shared_from.article_id if obj.shared_from else None

################### TOPICS, ArticlePublication ######################
class TopicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topics
        fields = '__all__'

class ArticlePublicationTopicSerializer(serializers.ModelSerializer):
    topic = TopicsSerializer(read_only=True)
    article = ArticleListSerializer(read_only=True)
    publication = PublicationSerializer(read_only=True)
    class Meta:
        model = ArticlePublicationTopic
        fields = '__all__'

################### COMMENT ######################
class CommentSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    article = ArticleListSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ['comment_id', 'user', 'article', 'comment_content', 'created_at', 'updated_at']

################### STAFF PICS ######################
class StaffPicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffPics
        fields = ['staff_pic_id', 'article','topic', 'publications', 'total_stories', 'total_saves', 'created_at', 'updated_at']

class ReadingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingList
        fields = ['reading_list_id', 'user', 'article', 'visibility', 'total_articles_in_lists_count','created_at', 'updated_at']


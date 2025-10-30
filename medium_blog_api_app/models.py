from django.db import models

# Create your models here.
class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, db_index=True)
    password = models.CharField(max_length=128)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True) 
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    is_writer = models.BooleanField(default=False)
    is_member = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_following = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    following_users = models.ManyToManyField('self',symmetrical=False,related_name='followers',blank=True)
    is_following_publications = models.BooleanField(default=False)
    followers_count = models.PositiveIntegerField(default=0)
    muted_authors = models.ManyToManyField('self', symmetrical=False, related_name='muted_by_users', blank=True)
    muted_publications = models.ManyToManyField('Publication', related_name='muted_by_users', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class Publication(models.Model):
    publication_id = models.AutoField(primary_key=True)
    publication_title = models.CharField(max_length=50)
    topic = models.ForeignKey('Topics', on_delete=models.SET_NULL, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_publications')
    editors = models.ManyToManyField(User, related_name='edited_publications', blank=True)
    writers = models.ManyToManyField(User, related_name="written_publications")
    short_note = models.TextField(blank=True, null=True)
    logo_image = models.ImageField(upload_to='publication_logos/', blank=True, null=True)
    followers = models.ManyToManyField(User, related_name="followed_publications")
    topics_of_publications = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_publications', null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='updated_publications', null=True)
    is_public = models.BooleanField(default=True)
    default_article_visibility = models.CharField(max_length=20,choices=[('public', 'Public'), ('private', 'Private')],default='public')
    def __str__(self):
        return self.publication_title

class Article(models.Model):
    article_id = models.AutoField(primary_key=True)
    publication = models.ForeignKey(Publication, on_delete=models.SET_NULL, related_name='articles', null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    article_title = models.CharField(max_length=255)
    article_subtitle = models.CharField(max_length=255, blank=True, null=True)
    article_content = models.TextField()
    article_category = models.CharField(max_length=50, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='article_images/', blank=True, null=True)
    video = models.URLField(blank=True, null=True)
    code_block = models.TextField(blank=True, null=True)
    read_time = models.IntegerField(default=0)
    is_member_only = models.BooleanField(default=False)
    published_at = models.DateTimeField(auto_now_add=True)
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='published_articles', null=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='updated_articles', null=True)
    clap_count = models.PositiveIntegerField(default=0)
    # clapped_by = models.ManyToManyField(User, related_name='clapped_articles', blank=True)
    comment_count = models.PositiveIntegerField(default=0)
    is_saved = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    show_less_like_this = models.BooleanField(default=False)

    def __str__(self):
        return self.article_title

## model for token blacklist(logout flow)
class TokenBlacklistLogout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=500, null=True, blank=True)
    is_expired = models.BooleanField(default=False, null=True, blank=True)
    expire_datetime = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.token
    
## user's reading list
class ReadingList(models.Model):
    reading_list_id = models.AutoField(primary_key=True)
    readinglist_title = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    visibility = models.CharField(max_length=20, choices=[('public', 'Public'), ('private', 'Private')], default='public')
    total_articles_in_lists_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,related_name='created_reading_lists', null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='updated_reading_lists',null=True)

    def __str__(self):
        return self.article

## Topics model
class Topics(models.Model):
    topic_id = models.AutoField(primary_key=True)
    topic_header_1 = models.CharField(max_length=50)
    topic_header_2 = models.CharField(max_length=50)
    topic_header_3 = models.CharField(max_length=50)
    topic_description = models.TextField()
    total_stories = models.IntegerField(default=0)
    total_followers = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,related_name='created_topics', null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,related_name='updated_topics', null=True)

    def __str__(self):
        return self.topic_header_1

## staff picks model
class StaffPics(models.Model):
    staff_pic_id = models.AutoField(primary_key=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topics, on_delete=models.CASCADE, null=True, blank=True)
    publications = models.ForeignKey(Publication, on_delete=models.CASCADE, null=True, blank=True)
    total_stories = models.DecimalField(max_digits=10, decimal_places=2, default=0) ## store total count  of total stories
    total_saves = models.DecimalField(max_digits=10, decimal_places=2, default=0) ## stores a total  count of total saves
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,related_name='created_staff_pics', null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,related_name='updated_staff_pics', null=True)

    def __str__(self):
        return self.article

class ArticlePublicationTopic(models.Model):
    apt_id = models.AutoField(primary_key=True)
    topic = models.ForeignKey(Topics, on_delete=models.CASCADE, related_name='apt_links')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, blank=True, null=True, related_name='apt_links')
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, blank=True, null=True, related_name='apt_links')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('topic', 'article', 'publication')

    def __str__(self):
        return f"APT: topic={self.topic.topic_header_1} article={self.article_id if self.article else None} pub={self.publication_id if self.publication else None}"

## Comment
class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    comment_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,related_name='created_comments', null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,related_name='updated_comments', null=True)

    def __str__(self):
        return self.comment_content
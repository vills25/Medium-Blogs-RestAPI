from django.db import models

# Create your models here.
class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(blank=True, null=True)
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)
    is_writer = models.BooleanField(default=False)
    is_following = models.BooleanField(default = False)
    is_member = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class Publication(models.Model):
    publication_id = models.AutoField(primary_key=True)
    publication_title = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_publications')  # Owner of publication
    editors = models.ManyToManyField(User, related_name='edited_publications', blank=True)
    writers = models.ManyToManyField(User, related_name="written_publications")
    short_note = models.TextField(blank=True, null=True)
    logo_image = models.ImageField(upload_to='publication_logos/', blank=True, null=True)
    followers = models.ManyToManyField(User, related_name="followed_publications")
    followers_count = models.PositiveIntegerField(default=0)
    topics_of_publications = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    default_article_visibility = models.CharField(max_length=20,choices=[('public', 'Public'), ('private', 'Private')],default='public')
    def __str__(self):
        return self.publication_title

class Article(models.Model):
    article_id = models.AutoField(primary_key=True)
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
    publication = models.ForeignKey(Publication, on_delete=models.SET_NULL, related_name='articles', null=True)
    is_member_only = models.BooleanField(default=False)
    published_at = models.DateTimeField(auto_now_add=True)
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='published_articles', null=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='updated_articles', null=True)
    clap_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    is_saved = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)

    def __str__(self):
        return self.title

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    visibility = models.CharField(max_length=20, choices=[('public', 'Public'), ('private', 'Private')], default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
from medium_blog_api_app.models import *
from medium_blog_api_app.serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from medium_blog_api_app.authentication.custom_jwt_auth import IsAuthenticatedCustom

## Create articles
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def create_article(request):
    user = request.user

    get_article_title = request.data.get('article_title')
    get_article_subtitle = request.data.get('article_subtitle')
    get_article_content = request.data.get('article_content')
    get_category = request.data.get('category')
    get_url = request.data.get('url')
    get_image = request.FILES.get('image')
    get_video = request.FILES.get('video')
    get_read_time = request.data.get('read_time')
    get_publication_date = request.data.get('publication')
    get_is_member_only = request.data.get('is_member_only')

    if not get_article_title or not get_article_subtitle or not get_article_content or not get_category or not get_url or not get_is_member_only:
        return Response({"status":"fail","message":"All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        article = Article.objects.create(
            author = user,
            article_title = get_article_title,
            article_subtitle = get_article_subtitle,
            article_content = get_article_content,
            article_category = get_category,
            url = get_url,
            image = get_image,
            video = get_video,
            read_time = get_read_time,
            publication_date = get_publication_date,
            is_member_only = get_is_member_only, 
        )
        article.save()
        # serializer = ArticleSerializer(article)
        return Response({"status":"success","message":"Article created successfully"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"status":"fail","message":str(e)}, status=status.HTTP_400_BAD_REQUEST)



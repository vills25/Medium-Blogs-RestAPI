from datetime import timezone
from medium_blog_api_app.models import *
from medium_blog_api_app.serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from medium_blog_api_app.authentication.custom_jwt_auth import *
from medium_blog_api_app.utils import *
from rest_framework import status
from django.db import transaction
from django.db.models import Q
import json
from rest_framework.permissions import AllowAny

## Create articles
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def create_article(request):

    get_title = request.data.get('article_title')
    get_content = request.data.get('article_content')
    get_subtitle = request.data.get('article_subtitle')
    get_category = request.data.get('article_category')
    get_publication_id = request.data.get('publication_id')
    get_url = request.data.get('url')
    get_img = request.FILES.get('image')
    get_video = request.data.get('video')
    get_code_block = request.data.get('code_block')
    get_is_member_only = request.data.get('is_member_only', False)
    get_topic_ids = request.data.get('topics', []) 

    if hasattr(request.data, 'getlist'):
        try:
            get_topic_ids = request.data.getlist('topics')
        except Exception:
            pass

    if isinstance(get_topic_ids, str):
        try:
            get_topic_ids = json.loads(get_topic_ids)
        except:
            get_topic_ids = [get_topic_ids]
    elif not isinstance(get_topic_ids, list):
        get_topic_ids = [get_topic_ids]

    if not get_title or not get_content:
        return Response({"status":"fail" ,"message":"article_title and article_content are required"}, status=status.HTTP_400_BAD_REQUEST)

    if get_img:
            validate_image(get_img)

    read_time = estimate_read_time(get_content)

    try:
        with transaction.atomic():
            publication = None
            if get_publication_id:
                try:
                    publication = Publication.objects.get(publication_id=int(get_publication_id))
                except Publication.DoesNotExist:
                    return Response({"status":"error","message":"publication not found"}, status=status.HTTP_404_NOT_FOUND)

            article = Article.objects.create(
                publication=publication,
                author=request.user,
                article_title=get_title,
                article_subtitle=get_subtitle,
                article_content=get_content,
                article_category=get_category,
                url=get_url,
                image=get_img,
                video=get_video,
                code_block=get_code_block,
                read_time=read_time,
                is_member_only=get_is_member_only,
                published_by=request.user,
                updated_by=request.user
            )

            for topic_name in get_topic_ids:
                topic_name = topic_name.strip()
                if not topic_name:
                    continue

                topic_obj, created = Topics.objects.create(topic_name=topic_name)
                ArticlePublicationTopic.objects.create(topic=topic_obj, article=article)
                topic_obj.total_stories += 1
                topic_obj.save()

            serializer = ArticleDetailSerializer(article, context={'request': request})
            return Response({"status":"success","message":"Article created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Update article
@api_view(['PUT'])
@permission_classes([IsAuthenticatedCustom])
def update_article(request):

    article_id = request.data.get('article_id')
    article_title = request.data.get('article_title')
    article_subtitle = request.data.get('article_subtitle')
    article_content = request.data.get('article_content')
    article_category = request.data.get('article_category')
    url = request.data.get('url')
    video = request.data.get('video')
    code_block = request.data.get('code_block')
    is_member_only = request.data.get('is_member_only')
    topics = request.data.get('topics')
    img = request.FILES.get('image')

    if not article_id:
        return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:

        article = Article.objects.get(article_id=int(article_id))

        is_owner = (article.author == request.user)
        is_pub_owner = (article.publication and article.publication.owner == request.user)
        is_admin = getattr(request.user, 'is_superuser', False) or False
        if not (is_owner or is_pub_owner or is_admin):
            return Response({"status":"error","message":"You do not have permission to update this article"}, status=status.HTTP_403_FORBIDDEN)

        if img:
            try:
                validate_image(img)
            except Exception as e:
                return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for field_name, value in [('article_title', article_title), 
                                      ('article_subtitle', article_subtitle), 
                                      ('article_content', article_content), 
                                      ('article_category', article_category), 
                                      ('url', url), 
                                      ('video', video), 
                                      ('code_block', code_block), 
                                      ('is_member_only', is_member_only)]:
                if value is not None:
                    setattr(article, field_name, value)
                
            if img:
                article.image = img
      
            if article_content:
                article.read_time = estimate_read_time(article_content)
      
            article.updated_at = timezone.now()
            article.updated_by = request.user
            article.save()

            if topics is not None:
                topic_ids = topics
                if isinstance(topic_ids, str):
                    import json
                    try:
                        topic_ids = json.loads(topic_ids)
                    except Exception:
                        topic_ids = [topic_ids]
                ArticlePublicationTopic.objects.filter(article=article).delete()
                for t in topic_ids:
                    try:
                        topic_obj = Topics.objects.get(topic_id=int(t))
                        ArticlePublicationTopic.objects.create(topic=topic_obj, article=article)
                    except Topics.DoesNotExist:
                        continue

        serializer = ArticleDetailSerializer(article, context={'request': request})
        return Response({"status":"success","message":"Article updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)

    except Article.DoesNotExist:
            return Response({"status":"error","message":"article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticatedCustom])
def delete_article(request):
    """
    Delete article (body contains article_id). Only author / publication owner / admin.
    """
    try:

        article_id = request.data.get('article_id')

        if not article_id:
            return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            article = Article.objects.get(article_id=int(article_id))
        except Article.DoesNotExist:
            return Response({"status":"error","message":"article not found"}, status=status.HTTP_404_NOT_FOUND)

        # --- PERMISSION CHECK ---
        is_owner = (article.author == request.user)
        is_pub_owner = (article.publication and article.publication.owner == request.user)
        is_admin = getattr(request.user,'is_superuser',False)
        if not (is_owner or is_pub_owner or is_admin):
            return Response({"status":"error","message":"You do not have permission to delete this article"}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            ArticlePublicationTopic.objects.filter(article=article).delete()
            article.delete()

        return Response({"status":"success","message":"Article deleted"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Search Articles
@api_view(['POST'])
@permission_classes([AllowAny])
def search_articles(request):
    """
    Search articles.
    """
    try:
        search_text = request.data.get('search_by_title')

        if not search_text:
            return Response({"status":"error","message":"search_text is required"}, status=status.HTTP_400_BAD_REQUEST)

        articles = Article.objects.all()
        if search_text:
            articles = articles.filter(Q(article_title__icontains=search_text) | Q(article_content__icontains=search_text))

        if not articles.exists():
            return Response({"status": "success", "message": "No articles found."},status=status.HTTP_404_NOT_FOUND)

        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        return Response({"status":"success","message":"Articles found", "results": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


## show my published articles
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def get_my_articles(request):
    try:
        articles = Article.objects.filter(author=request.user).order_by('-published_at').all()

        if not articles.exists():
            return Response({"status": "success", "message": "No articles found."},status=status.HTTP_404_NOT_FOUND)

        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        return Response({"status":"success","message":"Articles found", "results": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Display all articles from all users for dashboard
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_articles(request):
    try:
        articles = Article.objects.filter(is_reported=False, show_less_like_this = False).order_by('-published_at').all()

        if not articles.exists():
            return Response({"status": "success", "message": "No articles found."}, status=status.HTTP_404_NOT_FOUND)

        custom_data = []
        user = request.user if request.user.is_authenticated else None

        for article in articles:
            if article.is_member_only:
                if user and getattr(user, 'is_member', False):
                    content = article.article_content 
                    message = None
                else:
                    content = None  
                    message = "This article is for members only"
            else:
                content = article.article_content
                message = None

            custom_data.append({
                "article_id": article.article_id,
                "title": article.article_title,
                "subtitle": article.article_subtitle,
                "author": article.author.username,
                "publication": article.publication.publication_title if article.publication else None,
                "is_member_only": article.is_member_only,
                "message": message,
                "article_content": content,
                "published_at": article.published_at,
                "image": request.build_absolute_uri(article.image.url) if article.image else None,
                "url": article.url,
                "read_time": article.read_time,
                "clap_count": article.clap_count,
                "comment_count": article.comment_count
            })

        return Response({"status": "success","message": "Articles fetched","results": custom_data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Report an article (is_reported  = True)
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def report_article(request):
    get_article_id = request.data.get('article_id')
    report_article = request.data.get('report_article')
    if not get_article_id:
        return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        article = Article.objects.get(article_id=get_article_id)

        if report_article in ['true', 'True', True]:
            article.is_reported = True
        article.save()
        return Response({"status":"success","message":"Article reported"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## API for admin to see reported articles
@api_view(['GET'])
@permission_classes([IsAdminCustom])
def get_reported_articles(request):
    try:
        articles = Article.objects.filter(is_reported=True).order_by('-published_at').all()

        if not articles.exists():
            return Response({"status": "success", "message": "No articles found."},status=status.HTTP_404_NOT_FOUND)

        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        return Response({"status":"success","message":"Articles fatched", "data": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## mute/unmute author
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def mute_author(request):
    get_author_id = request.data.get('author_id')
    mute_author = request.data.get('mute_author')

    if not get_author_id:
        return Response({"status":"error","message":"author_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(user_id=get_author_id)

        if mute_author in ['true', 'True', True]:
            user.muted_authors = True
        else :
            user.muted_authors = False
        user.save()
        return Response({"status":"success","message":"Author: Firstname Lastname"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## mute/unmute publication
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def mute_publication(request):
    get_publication_id = request.data.get('publication_id')
    mute_publication = request.data.get('mute_publication')

    if not get_publication_id:
        return Response({"status":"error","message":"publication_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        publication = User.objects.get(user_id=get_publication_id)

        if mute_publication in ['true', 'True', True]:
            publication.muted_publications = True
        else :
            publication.muted_publications = False
        publication.save()
        return Response({"status":"success","message":"Publication muted"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## show less like this show_less_like_this = True
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def show_less_like_this_func(request):
    get_article_id = request.data.get('article_id')
    show_less_like_this = request.data.get('show_less_like_this')

    if not get_article_id:
        return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        article = Article.objects.get(article_id=get_article_id)

        if show_less_like_this in ['true', 'True', True]:
            article.show_less_like_this = True
        else :
            article.show_less_like_this = False
        article.save()
        return Response({"status":"success","message":"Show less like this"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
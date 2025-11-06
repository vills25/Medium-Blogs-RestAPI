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
from loguru import logger

## Create articles
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def create_article(request):
    """
    Create an article.
    """
    logger.info(f" Article creation attempt by user: {request.user.username}")

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
    get_allow_to_share_article = request.data.get('allow_to_share_article', False)
    get_topic_ids = request.data.get('topics', [])

    logger.debug(f"Article data - Title: {get_title}, Category: {get_category}, Publication: {get_publication_id}")


    try:
        if str(get_topic_ids).strip().startswith('['):
            get_topic_ids = json.loads(get_topic_ids)

        elif ',' in str(get_topic_ids):
            get_topic_ids = [t.strip() for t in str(get_topic_ids).split(',') if t.strip()]

        elif get_topic_ids:
            get_topic_ids = [str(get_topic_ids).strip()]
        else:
            get_topic_ids = []
    except:
        get_topic_ids = [str(get_topic_ids).strip()] if get_topic_ids else []

    if not get_title or not get_content:
        logger.warning("Article creation failed - Missing title or content")
        return Response({"status": "fail", "message": "article_title and article_content are required"},status=status.HTTP_400_BAD_REQUEST)

    if get_img:
        validate_image(get_img)

    read_time = estimate_read_time(get_content)

    try:
        with transaction.atomic():
            publication = None
            if get_publication_id:
                publication = Publication.objects.filter(publication_id=get_publication_id).first()
                if not publication:
                    logger.warning(f"Publication not found: {get_publication_id}")
                    return Response({"status": "error", "message": "publication not found"},status=status.HTTP_404_NOT_FOUND)

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
                allow_to_share_article=get_allow_to_share_article,
                published_by=request.user,
                updated_by=request.user
            )

            # --- Topic creation ---
            for topic_name in get_topic_ids:
                topic_name = str(topic_name).strip()
                if not topic_name:
                    continue
                topic_obj, created = Topics.objects.get_or_create(topic_name=topic_name)
                ArticlePublicationTopic.objects.create(topic=topic_obj, article=article)
                topic_obj.total_stories = topic_obj.total_stories + 1
                topic_obj.save()

            logger.success(f"Article created successfully: {get_title} (ID: {article.article_id})")
            serializer = ArticleDetailSerializer(article, context={'request': request})
            return Response({"status": "success", "message": "Article created successfully", "data": serializer.data},status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Article creation error: {str(e)}")
        return Response({"status": "error", "message": str(e)},status=status.HTTP_400_BAD_REQUEST)

## Update article
@api_view(['PUT'])
@permission_classes([IsAuthenticatedCustom])
def update_article(request):

    """
    Update article
    
    Parameters:
    article_id (int): article_id
    article_title (str): article_title
    article_subtitle (str): article_subtitle
    article_content (str): article_content
    article_category (str): article_category
    url (str): url
    video (str): video
    code_block (str): code_block
    is_member_only (bool): is_member_only
    topics (list): topics
    img (file): image
    allow_to_share_article (bool): allow_to_share_article
    """
    logger.info(f"Article update attempt by user: {request.user.username}")

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
    get_allow_to_share_article = request.data.get('allow_to_share_article', False)

    logger.debug(f"Update data - Article ID: {article_id}, Title: {article_title}")

    if not article_id:
        return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:

        article = Article.objects.get(article_id=int(article_id))

        is_owner = (article.author == request.user)
        is_pub_owner = (article.publication and article.publication.owner == request.user)
        is_admin = getattr(request.user, 'is_superuser', False) or False
        if not (is_owner or is_pub_owner or is_admin):
            logger.warning(f"Permission denied - User {request.user.username} cannot update article {article_id}")
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
                                      ('is_member_only', is_member_only),
                                      ('allow_to_share_article', get_allow_to_share_article)]:
                if value is not None:
                    setattr(article, field_name, value)
                
            if img:
                article.image = img
      
            if article_content:
                article.read_time = estimate_read_time(article_content)
      
            article.updated_at = timezone.now()
            article.updated_by = request.user
            article.save()
            logger.debug(f"Fields updated in article {article_id}")

            if topics is not None:
                topic_ids = topics
                if isinstance(topic_ids, str):
                    import json
                    try:
                        topic_ids = json.loads(topic_ids)
                    except Exception:
                        topic_ids = [topic_ids]
                ArticlePublicationTopic.objects.filter(article=article).delete()
                logger.debug("Existing topic links cleared")
                for t in topic_ids:
                    try:
                        topic_obj = Topics.objects.get(topic_id=int(t))
                        ArticlePublicationTopic.objects.create(topic=topic_obj, article=article)
                    except Topics.DoesNotExist:
                        continue

        logger.success(f" Article updated successfully: {article.article_title} (ID: {article.article_id})")
        serializer = ArticleDetailSerializer(article, context={'request': request})
        return Response({"status":"success","message":"Article updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)

    except Article.DoesNotExist:
            logger.warning(f"Article not found: {article_id}")
            return Response({"status":"error","message":"article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Article update error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticatedCustom])
def delete_article(request):
    """
    Delete article (body contains article_id). Only author / publication owner / admin.

    Request Body:
    {
        "article_id": "integer"
    }
    """

    logger.info(f"Article deletion attempt by user: {request.user.username}")
    article_id = request.data.get('article_id')

    if not article_id:
        return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:

        try:
            article = Article.objects.get(article_id=article_id)
            logger.debug(f"Article found: {article.article_title} (ID: {article.article_id})")
        except Article.DoesNotExist:
            logger.warning(f"Article not found: {article_id}")
            return Response({"status":"error","message":"article not found"}, status=status.HTTP_404_NOT_FOUND)

        # --- PERMISSION CHECK ---
        is_owner = (article.author == request.user)
        is_pub_owner = (article.publication and article.publication.owner == request.user)
        is_admin = getattr(request.user,'is_superuser',False)

        logger.debug(f"Permission check - Owner: {is_owner}, Pub Owner: {is_pub_owner}, Admin: {is_admin}")

        if not (is_owner or is_pub_owner or is_admin):
            logger.warning(f"Permission denied - User {request.user.username} cannot delete article {article_id}")
            return Response({"status":"error","message":"You do not have permission to delete this article"}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            ArticlePublicationTopic.objects.filter(article=article).delete()

            article.delete()
            logger.success(f" Article deleted successfully: {article.article_title} (ID: {article_id})")
            
        return Response({"status":"success","message":"Article deleted"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Article deletion error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Search Articles
@api_view(['POST'])
@permission_classes([AllowAny])
def search_articles(request):
    """
    Search articles.

    Request Body:
    {
        "search_by_title": "string"
    }

    Response:
    {
        "status": "success",
        "message": "Articles found",
        "results": [
            {
                "article_id": "integer",
                "article_title": "string",
                "article_subtitle": "string",
                "article_content": "string",
                "article_category": "string",
                "url": "string",
                "video": "string",
                "code_block": "string",
                "is_member_only": "boolean",
                "allow_to_share_article": "boolean",
                "image": "string",
                "created_at": "datetime",
                "updated_at": "datetime",
                "created_by": "string",
                "updated_by": "string",
                "published_at": "datetime",
                "published_by": "string",
                "clap_count": "integer",
    """

    logger.info(f"🔍 Article search attempt: '{search_text}'")

    search_text = request.data.get('search_by_title')

    if not search_text:
        logger.warning("Search failed - search_text required")
        return Response({"status":"error","message":"search_text is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:

        articles = Article.objects.all()
        if search_text:
            articles = articles.filter(Q(article_title__icontains=search_text) | Q(article_content__icontains=search_text))

        article_count = articles.count()
        logger.debug(f"Search found {article_count} articles")

        if not articles.exists():
            logger.info("No articles found for search")
            return Response({"status": "success", "message": "No articles found."},status=status.HTTP_404_NOT_FOUND)

        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        logger.success(f"Search completed: {article_count} articles found for '{search_text}'")
        return Response({"status":"success","message":"Articles found", "results": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## show my published articles
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def get_my_articles(request):
    """
    Show all articles published by the user.

    Response:
    {
        "status": "success",
        "message": "Articles found",
        "results": [
            {
                "article_id": "integer",
                "article_title": "string",
                "article_subtitle": "string",
                "article_content": "string",
                "article_category": "string",
                "url": "string",
                "video": "string",
                "code_block": "string",
                "is_member_only": "boolean",
                "allow_to_share_article": "boolean",
                "image": "string",
                "created_at": "datetime",
                "updated_at": "datetime",
                "created_by": "string",
                "updated_by": "string",
                "published_at": "datetime",
                "published_by": "string",
                "clap_count": "integer"
            }
        ]
    }
    """

    logger.info(f"My articles request by user: {request.user.username}")

    try:
        articles = Article.objects.filter(author=request.user).order_by('-published_at').all()

        if not articles.exists():
            return Response({"status": "success", "message": "No articles found."},status=status.HTTP_404_NOT_FOUND)

        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        logger.success(f"Retrieved articles for user: {request.user.username}")
        return Response({"status":"success","message":"Articles found", "results": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"My articles error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Display all articles from all users for dashboard
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_articles(request):   
    """
        Get all articles from all users for dashboard.

        Response:
        {
            "status": "success",
            "message": "Articles fetched",
            "results": [
                {
                    "article_id": "integer",
                    "title": "string",
                    "subtitle": "string",
                    "author": "string",
                    "publication": "string",
                    "is_member_only": "boolean",
                    "message": "string",
                    "article_content": "string",
                    "published_at": "datetime",
                    "image": "string",
                    "url": "string",
                    "read_time": "integer",
                    "clap_count": "integer",
                    "comment_count": "integer",
                    "is_shared": "boolean",
                    "original_article_id": "integer",
                    "total_shared": "integer"
                }
            ]
        }
    """

    user_info = request.user.username if request.user.is_authenticated else "Anonymous"
    logger.info(f"All articles request by: {user_info}")

    try:
        articles = Article.objects.filter(is_reported=False, show_less_like_this = False).order_by('-published_at').all()

        if not articles.exists():
            logger.info("No articles found in system")
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
                "comment_count": article.comment_count,
                "is_shared": True if article.shared_from else False,
                "original_article_id": article.shared_from.article_id if article.shared_from else None,
                "total_shared": article.share_count
            })
        logger.success(f"Dashboard data of {user_info}: {article.article_id}")
        return Response({"status": "success","message": "Articles fetched","results": custom_data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"All articles error: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Report an article (is_reported  = True)
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def report_article(request):
    """
    Report an article.

    Parameters:
    article_id (int): article_id
    report_article (bool): report_article
    """

    logger.info(f"Article report attempt by user: {request.user.username}")

    get_article_id = request.data.get('article_id')
    report_article = request.data.get('report_article')
    if not get_article_id:
        return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        article = Article.objects.get(article_id=get_article_id)

        if report_article in ['true', 'True', True]:
            article.is_reported = True
        article.save()
        logger.success(f"Article reported: {article.article_title} (ID: {article.article_id}) by {request.user.username}")
        return Response({"status":"success","message":"Article reported"}, status=status.HTTP_200_OK)

    except Article.DoesNotExist:
        logger.warning(f"Article not found for reporting: {get_article_id}")
        return Response({"status":"error","message":"Article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Article report error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## API for admin to see reported articles
@api_view(['GET'])
@permission_classes([IsAdminCustom])
def get_reported_articles(request):
    """
    Get all reported articles.
    """

    logger.info(f"Reported articles request by admin: {request.user.username}")

    try:
        articles = Article.objects.filter(is_reported=True).order_by('-published_at').all()

        if not articles.exists():
            logger.info("No reported articles found")
            return Response({"status": "success", "message": "No articles found."},status=status.HTTP_404_NOT_FOUND)

        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        logger.success(f"reported articles fetched by admin: {request.user.username}")
        return Response({"status":"success","message":"Articles fatched", "data": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Reported articles error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## mute/unmute author
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def mute_author(request):
    """
    Mute/Unmute an author.

    Request Body:
    {
        "author_id": "integer",
        "mute_author": "boolean"
    }

    """
    logger.info(f"Mute author attempt by user: {request.user.username}")

    get_author_id = request.data.get('author_id')
    mute_author = request.data.get('mute_author')

    if not get_author_id:
        logger.warning("Mute failed - author_id required")
        return Response({"status":"error","message":"author_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(user_id=get_author_id)

        if mute_author in ['true', 'True', True]:
            user.muted_authors = True
            logger.debug(f"Author muted: {user.username}")
        else :
            user.muted_authors = False
            logger.debug(f"Author unmuted: {user.username}")
        user.save()
        logger.success(f"Author muted/unmuted: {user.username} by {request.user.username}")
        return Response({"status":"success","message":f"Author: {user.username} has been muted."}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.warning(f"Author not found: {get_author_id}")
        return Response({"status":"error","message":"Author not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Mute author error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
## mute/unmute publication
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def mute_publication(request):
    """
    Mute/Unmute a publication.

    Request Body:
    {
        "publication_id": "integer",
        "mute_publication": "boolean"
    }
    """
    logger.info(f"Mute publication attempt by user: {request.user.username}")

    get_publication_id = request.data.get('publication_id')
    mute_publication = request.data.get('mute_publication')

    if not get_publication_id:
        logger.warning("Mute failed - publication_id required")
        return Response({"status":"error","message":"publication_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        publication = User.objects.get(user_id=get_publication_id)

        if mute_publication in ['true', 'True', True]:
            publication.muted_publications = True
            logger.debug(f"Publication muted: {publication.publication_title}")
        else :
            publication.muted_publications = False
            logger.debug(f"Publication unmuted: {publication.publication_title}")
        publication.save()
        logger.success(f"Publication muted/unmuted: {publication.publication_title} by {request.user.username}")
        return Response({"status":"success","message":"Publication muted"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Mute publication error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## show less like this show_less_like_this = True
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def show_less_like_this_func(request):
    
    """
    Mark an article as 'show less like this' or unmark it.

    Request Body:
    {
        "article_id": "integer",
        "show_less_like_this": "boolean"
    }
    """
    logger.info(f"Show less like this attempt by user: {request.user.username}")
    get_article_id = request.data.get('article_id')
    show_less_like_this = request.data.get('show_less_like_this')

    if not get_article_id:
        logger.warning("Show less like this failed - article_id required")
        return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        article = Article.objects.get(article_id=get_article_id)

        if show_less_like_this in ['true', 'True', True]:
            article.show_less_like_this = True
            logger.debug(f"Show less enabled for: {article.article_title}")
        else :
            article.show_less_like_this = False
            logger.debug(f"Show less disabled for: {article.article_title}")

        article.save()
        logger.success(f"Show less like this: {article.article_title} by {request.user.username}")
        return Response({"status":"success","message":f"Show less like this turned {'on' if article.show_less_like_this else 'off'}"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Show less like this error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Share API
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def share_article(request):

    """
    Share an article.

    Parameters:
    article_id (int): article_id

    """
    logger.info(f"Share article attempt by user: {request.user.username}")
    user = request.user
    get_article_id = request.data.get("article_id")

    if not get_article_id:
        logger.warning("Share article failed - article_id required")
        return Response({"status": "error", "message": "article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        original_article = Article.objects.get(article_id = get_article_id)

        with transaction.atomic():
            shared_article = Article.objects.create(
                publication = original_article.publication,
                author = user,
                article_title = original_article.article_title,
                article_subtitle = original_article.article_subtitle,
                article_content = original_article.article_content,
                article_category = original_article.article_category,
                url = original_article.url,
                image = original_article.image,
                video = original_article.video,
                code_block = original_article.code_block,
                read_time = original_article.read_time,
                is_member_only = original_article.is_member_only,
                published_by = user,
                shared_from = original_article,
                shared_by = user,
                allow_to_share_article = True
            )

            original_article.share_count += 1
            original_article.save()

            logger.success(f"✅ Article shared successfully: {original_article.article_title} -> {shared_article.article_id} by {user.username}")
            serializer = ArticleFeedSerializer(shared_article)
            return Response({"status": "success","message": "Article shared successfully.","shared_article": serializer.data}, status=status.HTTP_200_OK)

    except Article.DoesNotExist:
        logger.warning(f"Article not found for sharing: {get_article_id}")
        return Response({"status": "fail", "message": "Article not found."}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Share article error: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

## undo reshare
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def undo_reshare(request):

    """
    Undo reshare an article.

    Parameters:
    article_id (int): article_id
    undo_reshare (bool): undo_reshare

    }
    """

    logger.info(f"Undo reshare attempt by user: {request.user.username}")
    get_article_id = request.data.get('article_id')
    undo_reshare = request.data.get('undo_reshare')

    if not get_article_id:
        logger.warning("Undo reshare failed - article_id required")
        return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        article = Article.objects.get(article_id=get_article_id)

        if undo_reshare in ['true', 'True', True]:
            article.allow_to_share_article = True
            action = "on"
            logger.debug(f"Reshare enabled for: {article.article_title}")
        else :
            article.allow_to_share_article = False
            action = "off"
            logger.debug(f"Reshare disabled for: {article.article_title}")

        article.save()
        logger.success(f"Undo reshare turned {action} for article: {article.article_title}")
        return Response({"status":"success","message":f"Undo reshare turned {'on' if article.allow_to_share_article else 'off'}"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Undo reshare error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## GET only shared articles
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def get_shared_articles(request):
    
    """
    Get all shared articles.
    """
    logger.info(f"Shared articles request by user: {request.user.username}")
    try:
        articles = Article.objects.filter(shared_from__isnull=False).order_by('-published_at').all()

        if not articles.exists():
            logger.info("No shared articles found")
            return Response({"status": "success", "message": "No articles found."},status=status.HTTP_404_NOT_FOUND)

        shared_count = articles.count()
        logger.success(f"Fetched {shared_count} shared articles")

        serializer = ArticleFeedSerializer(articles, many=True, context={'request': request})
        return Response({"status":"success","message":"Articles found", "results": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Get shared articles error: {str(e)}")
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

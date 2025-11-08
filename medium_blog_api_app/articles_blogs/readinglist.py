# from datetime import timezone
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from medium_blog_api_app.authentication.custom_jwt_auth import IsAuthenticatedCustom, IsAdminCustom
from medium_blog_api_app.models import *
from medium_blog_api_app.serializers import *
from django.db import transaction
from django.db.models import Q
from medium_blog_api_app.utils import validate_image
from django.db.models import F
from loguru import logger

#################### READINGLIST #####################
## Create readinglist
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def create_readinglist(request):
    """
    Create readinglist.

    Parameters:
    article_id (int): article_id
    visibility (string): visibility of the reading list
    """
    article_id = request.data.get('article_id')
    visibility = request.data.get('visibility', 'public')

    logger.info(f"Create readinglist attempt by user: {request.user.username} with article_id: {article_id} and visibility: {visibility}")

    if not article_id:
            return Response({"status": "error", "message": "article_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        article = Article.objects.get(article_id = article_id)

        if ReadingList.objects.filter(user=request.user, article=article).exists():
            logger.warning(f"User {request.user.username} already has this article in their reading list")
            return Response({"status": "fail","message": "This article is already in your reading list"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            readinglist = ReadingList.objects.create(
                article_id = article_id,
                visibility = visibility,
                user = request,
                created_at = timezone.now(),
                created_by = request.user,
                updated_at = timezone.now(),
                updated_by = request.user
            )

            ## count total articles in readinglist
            ReadingList.objects.filter(user=request.user).update(total_articles_in_lists_count=F('total_articles_in_lists_count') + 1)

            logger.success(f"Readinglist created by user: {request.user.username} with article_id: {article_id} and visibility: {visibility}")
        serializer = ReadingListSerializer(readinglist, context={'request': request})
        return Response({"status": "success", "message": "Readinglist created", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except Article.DoesNotExist:
        logger.warning(f"Article not found: {article_id}")
        return Response({"status": "error", "message": "Article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error creating readinglist: {e}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Get readinglist
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def get_readinglist(request):

    logger.info(f"Get readinglist request by user: {request.user.username}")
    try:
        readinglist = ReadingList.objects.filter(user = request.user).all().order_by('-created_at')
        serializer = ReadingListSerializer(readinglist, many=True, context={'request': request})
        
        logger.success(f"Readinglist found for user: {request.user.username}")
        return Response({"status": "success", "message": "Readinglist found", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except ReadingList.DoesNotExist:
        logger.warning(f"Readinglist not found for user: {request.user.username}")
        return Response({"status": "error", "message": "Readinglist not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error getting readinglist: {e}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Edit readinglist
@api_view(['PUT'])
@permission_classes([IsAuthenticatedCustom])
def edit_readinglist(request):

    readinglist_id = request.data.get('readinglist_id')
    visibility = request.data.get('visibility', 'public')

    if not readinglist_id:
        return Response({"status": "error", "message": "readinglist_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Edit readinglist attempt by user: {request.user.username} with readinglist_id: {readinglist_id} and visibility: {visibility}")

    try:
        with transaction.atomic():
            readinglist = ReadingList.objects.get(readinglist_id = readinglist_id)

            readinglist.visibility = visibility
            readinglist.updated_at = timezone.now()
            readinglist.updated_by = request.user
            readinglist.save()

            logger.success(f"Readinglist updated by user: {request.user.username} with readinglist_id: {readinglist_id} and visibility: {visibility}")

        serializer = ReadingListSerializer(readinglist, context={'request': request})
        return Response({"status": "success", "message": "Readinglist updated", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except ReadingList.DoesNotExist:
        logger.warning(f"Readinglist not found: {readinglist_id}")
        return Response({"status": "error", "message": "Readinglist not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error updating readinglist: {e}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Delete readinglist
@api_view(['DELETE'])
@permission_classes([IsAuthenticatedCustom])
def delete_readinglist(request):

    """
    Delete a reading list item.

    Request Body:
    {
        "readinglist_id": 12
    }
    """
    readinglist_id = request.data.get('readinglist_id')

    if not readinglist_id:
        return Response({"status": "error", "message": "readinglist_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Delete readinglist attempt by user: {request.user.username} with readinglist_id: {readinglist_id}")

    try:
        with transaction.atomic():
            readinglist = ReadingList.objects.get(readinglist_id = readinglist_id)

            readinglist.delete()

            logger.success(f"Readinglist deleted by user: {request.user.username} with readinglist_id: {readinglist_id}")

            ReadingList.objects.filter(user=request.user).update(total_articles_in_lists_count=F('total_articles_in_lists_count') - 1)

        return Response({"status": "success", "message": "Readinglist deleted"}, status=status.HTTP_200_OK)
    
    except ReadingList.DoesNotExist:
        logger.warning(f"Readinglist not found: {readinglist_id}")
        return Response({"status": "error", "message": "Readinglist not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error deleting readinglist: {e}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Add Multiple Articles to Reading List
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def add_multiple_to_readinglist(request):
    """
    Add multiple articles to reading list at once.

    Request Body:
    {
        "article_ids": [25, 30, 35],
        "visibility": "public"
    }
    """
    article_ids = request.data.get('article_ids', [])
    visibility = request.data.get('visibility', 'public')

    if not article_ids:
        return Response({"status": "error","message": "article_ids is required"}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Add multiple articles to readinglist attempt by user: {request.user.username} with article_ids: {article_ids} and visibility: {visibility}")

    try:

        try:

            if ',' in str(article_ids):
                article_ids = [int(a.strip()) for a in str(article_ids).split(',') if a.strip().isdigit()]

            elif str(article_ids).isdigit():
                article_ids = [int(article_ids)]

            else:
                article_ids = [int(a) for a in article_ids]
        except Exception:
            logger.error(f"Invalid article_ids format: {article_ids}")
            return Response({"status": "error","message": "Invalid article_ids format"}, status=status.HTTP_400_BAD_REQUEST)

        added_count = 0
        skipped_count = 0

        with transaction.atomic():
            for article_id in article_ids:
                try:
                    article = Article.objects.get(article_id=article_id)

                    if ReadingList.objects.filter(user=request.user, article=article).exists():
                        skipped_count += 1
                        continue

                    ReadingList.objects.create(
                        article=article,
                        visibility=visibility,
                        user=request.user,
                        created_by=request.user,
                        updated_by=request.user
                    )
                    added_count += 1

                except Article.DoesNotExist:
                    skipped_count += 1
                    continue

            total_articles = ReadingList.objects.filter(user=request.user).count()
        logger.success(f"Multiple articles added to readinglist by user: {request.user.username} with article_ids: {article_ids} and visibility: {visibility}")
        return Response({
            "status": "success","message": f"{added_count} articles added to reading list","data": {"added_count": added_count,"skipped_count": skipped_count,
                                         "total_articles_in_list": total_articles}}, status=status.HTTP_200_OK)

    except Article.DoesNotExist:
        logger.warning(f"Article not found: {article_ids}")
        return Response({"status": "error","message": "Article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error adding multiple articles to readinglist: {e}")
        return Response({"status": "error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Clear Reading List
@api_view(['DELETE'])
@permission_classes([IsAuthenticatedCustom])
def clear_readinglist(request):
    """
    Clear entire reading list.
    """
    user = request.user
    get_reading_list_id = request.data.get('readinglist_id')

    if not get_reading_list_id:
        return Response({"status": "error", "message": "readinglist_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Clear readinglist attempt by user: {request.user.username} with readinglist_id: {get_reading_list_id}")

    try:
        with transaction.atomic():
            deleted_count = ReadingList.objects.filter(reading_list_id = get_reading_list_id).count()

            delete_readinglist = ReadingList.objects.filter(user=user)
            delete_readinglist.delete()

            logger.success(f"Readinglist cleared by user: {request.user.username} with readinglist_id: {get_reading_list_id}")

            ReadingList.objects.filter(user=user).update(total_articles_in_lists_count=F('total_articles_in_lists_count') - deleted_count)

        return Response({"status": "success","message": "Reading list cleared successfully","data": {"deleted_count": deleted_count,"total_articles_removed": deleted_count}
                            }, status=status.HTTP_200_OK)

    except ReadingList.DoesNotExist:
        logger.warning(f"Readinglist not found: {get_reading_list_id}")
        return Response({"status": "error", "message": "Readinglist not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error clearing readinglist: {e}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Search in Reading List
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def search_readinglist(request):
    """
    Search articles in reading list.

    Request Body:
    {
        "search_text": "python"
    }
    """
    user = request.user
    search_text = request.data.get('search_text')

    if not search_text:
        return Response({"status": "error", "message": "search_text is required"}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Search readinglist attempt by user: {request.user.username} with search_text: {search_text}")

    try:

        reading_list_items = ReadingList.objects.filter(user=user).filter(
                                        Q(article__article_title__icontains=search_text) |
                                        Q(article__article_content__icontains=search_text) |
                                        Q(article__article_category__icontains=search_text)
                                    ).select_related('article')

        search_results = []
        for item in reading_list_items:
            match_reason = []
            if search_text.lower() in item.article.article_title.lower():
                match_reason.append("Title contains search text")
            if search_text.lower() in item.article.article_content.lower():
                match_reason.append("Content contains search text")
            if search_text.lower() in (item.article.article_category or "").lower():
                match_reason.append("Category contains search text")
            
            search_results.append({
                "reading_list_id": item.reading_list_id,
                "article_id": item.article.article_id,
                "article_title": item.article.article_title,
                "article_category": item.article.article_category,
                "visibility": item.visibility,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "match_reason": ", ".join(match_reason) if match_reason else "Relevant match"
            })

        if not search_results:
            return Response({"status": "error", "message": "No search results found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"status": "success","message": "Search results found","data": search_results}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error searching readinglist: {e}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Get Reading List Stats
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def get_readinglist_stats(request):
    """
    Get reading list statistics.
    """
    
    get_user = request.user
    logger.info(f"Get readinglist stats attempt by user: {request.user.username}")
    try:
        reading_list_items = ReadingList.objects.filter(user=get_user).select_related('article')
        
        total_articles = reading_list_items.count()
        public_articles = reading_list_items.filter(visibility='public').count()
        private_articles = reading_list_items.filter(visibility='private').count()
        
        total_read_time = 0
        categories = {}
        
        for item in reading_list_items:
            total_read_time += item.article.read_time if item.article.read_time else 0
            
            category = item.article.article_category
            if category:
                categories[category] = categories.get(category, 0) + 1
        
        last_added = reading_list_items.order_by('-created_at').first()
        
        stats_data = {
            "total_articles": total_articles,
            "public_articles": public_articles,
            "private_articles": private_articles,
            "total_read_time": total_read_time,
            "categories": categories,
            "last_added": last_added.created_at if last_added else None
        }

        return Response({"status": "success", "message": "Reading list stats fetched","data": stats_data}, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting readinglist stats: {e}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
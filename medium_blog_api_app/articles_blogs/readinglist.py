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

#################### READINGLIST #####################
## Create readinglist
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def create_readinglist(request):
    article_id = request.data.get('article_id')
    visibility = request.data.get('visibility', 'public')

    if not article_id:
            return Response({"status": "error", "message": "article_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        article = Article.objects.get(article_id = article_id)

        if ReadingList.objects.filter(user=request.user, article=article).exists():
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

        serializer = ReadingListSerializer(readinglist, context={'request': request})
        return Response({"status": "success", "message": "Readinglist created", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except Article.DoesNotExist:
        return Response({"status": "error", "message": "Article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

## Get readinglist
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def get_readinglist(request):
    try:
        readinglist = ReadingList.objects.filter(user = request.user).all().order_by('-created_at')
        serializer = ReadingListSerializer(readinglist, many=True, context={'request': request})
        return Response({"status": "success", "message": "Readinglist found", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
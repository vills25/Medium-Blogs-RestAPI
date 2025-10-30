from datetime import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from medium_blog_api_app.authentication.custom_jwt_auth import IsAuthenticatedCustom
from medium_blog_api_app.models import *
from medium_blog_api_app.serializers import *


## Give Clap to articles
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def give_clap(request):
    try:
        article_id = request.data.get('article_id')

        if not article_id:
            return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # no doublr clap check
        if Article.objects.filter(article_id=article_id, clap_count=request.user).exists():
            return Response({"status":"error","message":"You already clapped this article"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            article = Article.objects.get(article_id=int(article_id))
        except Article.DoesNotExist:
            return Response({"status":"error","message":"article not found"}, status=status.HTTP_404_NOT_FOUND)

        article.clap_count += 1
        article.save()
        return Response({"status":"success","message":"Calpped"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## Remove clap to articles
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def remove_clap(request):
    try:
        article_id = request.data.get('article_id')

        if not article_id:
            return Response({"status":"error","message":"article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            article = Article.objects.get(article_id=int(article_id))
        except Article.DoesNotExist:
            return Response({"status":"error","message":"article not found"}, status=status.HTTP_404_NOT_FOUND)

        article.clap_count -= 1
        article.save()
        return Response({"status":"success","message":"Calp removed"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## add comment to article
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def add_comment(request):
    try:
        article_id = request.data.get('article_id')
        content = request.data.get('content')

        if not article_id or not content:
            return Response({"status":"error","message":"article_id and content required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            article = Article.objects.get(article_id=int(article_id))
        except Article.DoesNotExist:
            return Response({"status":"error","message":"article not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():  
            comment = Comment.objects.create(
                user=request.user, 
                article=article, 
                comment_content=content
                )
            serializer = CommentSerializer(comment, context={'request': request})
            return Response({"status":"success","message":"Comment added", "data": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Comment Edit
@api_view(['PUT'])
@permission_classes([IsAuthenticatedCustom])
def edit_comment(request):
    try:
        comment_id = request.data.get('comment_id')
        content = request.data.get('content')

        if not comment_id or not content:
            return Response({"status":"error","message":"comment_id and content required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = Comment.objects.get(comment_id=int(comment_id), user=request.user)
        except Comment.DoesNotExist:
            return Response({"status":"error","message":"comment not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            comment.comment_content = content
            comment.updated_at = timezone.now()
            comment.save()
            serializer = CommentSerializer(comment, context={'request': request})
            return Response({"status":"success","message":"Comment updated", "data": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## remove comment from article
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def remove_comment(request):
    try:
        comment_id = request.data.get('comment_id')

        if not comment_id:
            return Response({"status":"error","message":"comment_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = Comment.objects.get(comment_id=int(comment_id))
        except Comment.DoesNotExist:
            return Response({"status":"error","message":"comment not found"}, status=status.HTTP_404_NOT_FOUND)

        comment.delete()
        return Response({"status":"success","message":"Comment removed"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status":"error","message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


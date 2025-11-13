from datetime import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from medium_blog_api_app.authentication.custom_jwt_auth import IsAuthenticatedCustom
from medium_blog_api_app.models import *
from medium_blog_api_app.serializers import *
from loguru import logger

# Give Clap to articles
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def give_clap(request):
    """
    Give a clap to an article.
    """
    user = request.user
    logger.info(f"Clap attempt by user: {user.username}")

    article_id = request.data.get('article_id')

    if not article_id:
        logger.warning("Clap failed - article_id required")
        return Response({"status": "error", "message": "article_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        
        article = Article.objects.get(article_id=article_id)

        # Check if user already clapped this article
        if Article.objects.filter(article_id=article_id, clapped_by = user).exists():
            logger.warning(f"User {user.username} already clapped article {article_id}")
            return Response({"status": "error", "message": "You already clapped this article"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            article = Article.objects.get(article_id=article_id)
            logger.debug(f"Article found: {article.article_title} (ID: {article.article_id})")

            with transaction.atomic():
                # article.clap_count += 1
                # article.save()
                article.clapped_by.add(user)
                article.clap_count = article.clapped_by.count()
                article.save()
                
                logger.success(f"Clap added to article '{article.article_title}' by user {user.username}")
                return Response({"status": "success", "message": "Clapped"}, status=status.HTTP_200_OK)

        except Article.DoesNotExist:
            logger.warning(f"Article not found: {article_id}")
            return Response({"status": "error", "message": "article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.exception(f"Clap error: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Remove clap from articles
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def remove_clap(request):
    """
    Remove a clap from an article.
    """
    logger.info(f"Remove clap attempt by user: {request.user.username}")

    try:
        article_id = request.data.get('article_id')

        if not article_id:
            logger.warning("Remove clap failed - article_id required")
            return Response({"status": "error", "message": "article_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            article = Article.objects.get(article_id=int(article_id))
            logger.debug(f"Article found: {article.article_title} (ID: {article.article_id})")

            if article.clap_count > 0:
                article.clap_count -= 1
                article.save()
                logger.success(f"Clap removed from article '{article.article_title}' by user {request.user.username}")
            else:
                logger.warning(f"Clap count already zero for article '{article.article_title}'")

            return Response({"status": "success", "message": "Clap removed"}, status=status.HTTP_200_OK)

        except Article.DoesNotExist:
            logger.warning(f"Article not found: {article_id}")
            return Response({"status": "error", "message": "article not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception(f"Remove clap error: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Add comment to article
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def add_comment(request):
    """
    Add a comment to an article.
    """
    logger.info(f"Add comment attempt by user: {request.user.username}")

    try:
        article_id = request.data.get('article_id')
        content = request.data.get('content')

        if not article_id or not content:
            logger.warning("Add comment failed - article_id and content required")
            return Response({"status": "error", "message": "article_id and content required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            article = Article.objects.get(article_id=int(article_id))
            logger.debug(f"Article found: {article.article_title} (ID: {article.article_id})")
        except Article.DoesNotExist:
            logger.warning(f"Article not found: {article_id}")
            return Response({"status": "error", "message": "article not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            comment = Comment.objects.create(
                user=request.user,
                article=article,
                comment_content=content
            )

            article.comment_count += 1
            article.save()

            logger.debug(f"Comment created: ID {comment.comment_id}")
            logger.success(f"Comment added to article '{article.article_title}' by user {request.user.username}")

            serializer = CommentSerializer(comment, context={'request': request})
            return Response({"status": "success", "message": "Comment added", "data": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Add comment error: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Comment Edit
@api_view(['PUT'])
@permission_classes([IsAuthenticatedCustom])
def edit_comment(request):
    """
    Edit a comment.
    """
    logger.info(f"Edit comment attempt by user: {request.user.username}")

    try:
        comment_id = request.data.get('comment_id')
        content = request.data.get('content')

        if not comment_id or not content:
            logger.warning("Edit comment failed - comment_id and content required")
            return Response({"status": "error", "message": "comment_id and content required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = Comment.objects.get(comment_id=int(comment_id), user=request.user)
            logger.debug(f"Comment found: ID {comment_id} by user {request.user.username}")
        except Comment.DoesNotExist:
            logger.warning(f"Comment not found or user not authorized: {comment_id}")
            return Response({"status": "error", "message": "comment not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            old_content = comment.comment_content
            comment.comment_content = content
            comment.updated_at = timezone.now()
            comment.save()

            logger.debug(f"Comment updated - Old: {old_content} New: {content}")
            logger.success(f"Comment {comment_id} updated by user {request.user.username}")

            serializer = CommentSerializer(comment, context={'request': request})
            return Response({"status": "success", "message": "Comment updated", "data": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Edit comment error: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Remove comment from article
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def remove_comment(request):
    """
    Remove a comment from an article.
    """
    logger.info(f"Remove comment attempt by user: {request.user.username}")

    try:
        comment_id = request.data.get('comment_id')

        if not comment_id:
            logger.warning("Remove comment failed - comment_id required")
            return Response({"status": "error", "message": "comment_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = Comment.objects.get(comment_id=comment_id)
            logger.debug(f"Comment found: ID {comment_id} on article {comment.article.article_id}")
        except Comment.DoesNotExist:
            logger.warning(f"Comment not found: {comment_id}")
            return Response({"status": "error", "message": "comment not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if user owns the comment or is admin
        if comment.user != request.user and not getattr(request.user, 'is_admin', False):
            logger.warning(f"User {request.user.username} not authorized to delete comment {comment_id}")
            return Response({"status": "error", "message": "You are not authorized to delete this comment"}, status=status.HTTP_403_FORBIDDEN)

        article_id = comment.article.article_id
        comment.delete()

        try:
            article = Article.objects.get(article_id=article_id)
            if article.comment_count > 0:
                article.comment_count -= 1
                article.save()
                logger.debug(f"Article comment count updated: {article.comment_count}")
        except Article.DoesNotExist:
            logger.warning(f"Article not found while updating comment count: {article_id}")

        logger.success(f"Comment {comment_id} removed by user {request.user.username}")
        return Response({"status": "success", "message": "Comment removed"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Remove comment error: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Get user comments
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def get_my_comments(request):
    """
    Get all comments by the current user.
    """
    logger.info(f"Get user comments request by user: {request.user.username}")

    try:
        comments = Comment.objects.filter(user=request.user).select_related('article').order_by('-created_at')
        comment_count = comments.count()

        logger.debug(f"Found {comment_count} comments by user {request.user.username}")

        if comment_count == 0:
            logger.info(f"No comments found for user {request.user.username}")
            return Response({"status": "success", "message": "No comments found", "data": []}, status=status.HTTP_200_OK)

        serializer = CommentSerializer(comments, many=True, context={'request': request})
        logger.success(f"Retrieved {comment_count} comments for user {request.user.username}")
        return Response({"status": "success", "message": "Comments retrieved", "data": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Get user comments error: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

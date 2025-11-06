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
from loguru import logger

#################### TOPICS #####################
## Create topics
@api_view(['POST'])
@permission_classes([IsAdminCustom])
def create_topic(request):
    """
    Create topic.

    Request Body:
    {
        "topic_header_1": "string",
        "topic_header_2": "string",
        "topic_header_3": "string",
        "topic_description": "string"
    }
    """
    user = request.user
    try:
        logger.info(f"Creating topic - User: {user.username}")
        header1 = request.data.get('topic_header_1')
        if not header1:
            logger.warning("Topic creation failed - topic_header_1 is required")
            return Response({"status": "error", "message": "topic_header_1 is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        header2 = request.data.get('topic_header_2', '')
        header3 = request.data.get('topic_header_3', '')
        desc = request.data.get('topic_description', '')

        with transaction.atomic():
            topic = Topics.objects.create(
                topic_header_1 = header1,
                topic_header_2 = header2,
                topic_header_3 = header3,
                topic_description = desc,
                created_by = request.user,
                updated_by = request.user
            )
        logger.info(f"Topic created successfully - Topic ID: {topic.topic_id}")
        serializer = TopicsSerializer(topic, context={'request': request})
        return Response({"status": "success", "message": "Topic created", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error creating topic: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Edit topics
@api_view(['PUT'])
@permission_classes([IsAdminCustom])
def edit_topic(request):
    
    """
    Edit topic.

    Request Body:
    {
        "topic_id": "integer",
        "topic_header_1": "string",
        "topic_header_2": "string",
        "topic_header_3": "string",
        "topic_description": "string"
    }
    """
    try:
        logger.info(f"Editing topic - User: {request.user.user_id}")
        topic_id = request.data.get('topic_id')
        header1 = request.data.get('topic_header_1')
        header2 = request.data.get('topic_header_2', '')
        header3 = request.data.get('topic_header_3', '')
        topic_description = request.data.get('topic_description', '')

        if not topic_id:
            logger.warning("Topic edit failed - topic_id is required")
            return Response({"status": "error", "message": "topic_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        topic = Topics.objects.get(topic_id = topic_id)

        with transaction.atomic():
            topic.topic_header_1 = header1
            topic.topic_header_2 = header2
            topic.topic_header_3 = header3
            topic.topic_description = topic_description
            topic.updated_by = request.user
            topic.save()
        
        logger.info(f"Topic updated successfully - Topic ID: {topic.topic_id}")
        serializer = TopicsSerializer(topic, context={'request': request})
        return Response({"status": "success", "message": "Topic updated", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except Topics.DoesNotExist:
        logger.warning(f"Topic not found for editing - Topic ID: {topic_id}")
        return Response({"status": "error", "message": "topic not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error editing topic: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## Delete topics
@api_view(['DELETE'])
@permission_classes([IsAdminCustom])
def delete_topic(request):
    
    """
    Delete topic (body contains topic_id). Only admin can delete topics.

    Request Body:
    {
        "topic_id": "integer"
    }
    """
    try:
        logger.info(f"Deleting topic - User: {request.user.user_id}")
        topic_id = request.data.get('topic_id')

        if not topic_id:
            logger.warning("Topic deletion failed - topic_id is required")
            return Response({"status": "error", "message": "topic_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            topic = Topics.objects.get(topic_id = topic_id)
            topic.delete()

        logger.info(f"Topic deleted successfully - Topic ID: {topic_id}")
        return Response({"status": "success", "message": "Topic deleted"}, status=status.HTTP_200_OK)
    
    except Topics.DoesNotExist:
        logger.warning(f"Topic not found for deletion - Topic ID: {topic_id}")
        return Response({"status": "error", "message": "topic not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error deleting topic: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## view all topics
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def view_all_topics(request):
    """
    View all topics.

    Request Body: None
    """
    try:
        logger.info(f"Viewing all topics - User: {request.user.user_id}")
        topics = Topics.objects.all()
        serializer = TopicsSerializer(topics, many=True, context={'request': request})
        logger.info(f"Successfully fetched {len(topics)} topics")
        return Response({"status": "success", "message": "Topics fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error viewing all topics: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## search topics
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def search_topics(request):

    """
    Search topics.

    Request Body:
    {
        "enter_text": "string"
    }
    """
    search_topic = request.data.get('enter_text')
    if not search_topic:
        logger.warning("Topic search failed - enter_text is required")
        return Response({"status": "error", "message": "enter_text is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        logger.info(f"Searching topics - Search term: '{search_topic}' - User: {request.user.user_id}")
        topics = Topics.objects.filter(Q(topic_header_1__icontains=search_topic) | 
                                       Q(topic_header_2__icontains=search_topic) | 
                                       Q(topic_header_3__icontains=search_topic) | 
                                       Q(topic_description__icontains=search_topic))

        serializer = TopicsSerializer(topics, many=True, context={'request': request})
        logger.info(f"Topic search completed - Found {len(topics)} results")
        return Response({"status": "success", "message": "Topics fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error searching topics: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#################### PUBLICATION #####################
## Create publications
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def create_publication(request):
    """
    Create publication.

    Request Body:
    {
        "publication_title": "string",
        "topic_id": "integer",
        "short_note": "string",
        "logo_image": "file",
        "topics_of_publications": "string",
        "is_public": "bool",
        "default_article_visibility": "string"
    }
    """
    try:
        logger.info(f"Creating publication - User: {request.user.user_id}")

        get_publication_title = request.data.get('publication_title')
        get_topic_id = request.data.get('topic_id')
        get_short_note = request.data.get('short_note')
        get_logo_image = request.FILES.get('logo_image')
        get_topics_of_publications = request.data.get('topics_of_publications') # Enter topics id or topics name
        get_default_article_visibility = request.data.get('default_article_visibility','public')

        if not get_publication_title:
            logger.warning("Publication creation failed - publication_title is required")
            return Response({"status": "error", "message": "publication_name is required"}, status=status.HTTP_400_BAD_REQUEST)

        topic = None
        if get_topic_id:
            topic = Topics.objects.filter(topic_id = get_topic_id).first()

        if get_logo_image:
            try:
                validate_image(get_logo_image)
            except Exception as e:
                logger.warning(f"Image validation failed: {str(e)}")
                return Response({"status":"fail","message":str(e)}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            publication = Publication.objects.create(
                publication_title = get_publication_title,
                topic = topic,
                owner = request.user,
                short_note = get_short_note,
                logo_image = get_logo_image,
                topics_of_publications = get_topics_of_publications,
                created_by = request.user,
                updated_by = request.user,
                is_public = request.data.get('is_public', True),
                default_article_visibility = get_default_article_visibility # Enter topics id or topics name
            )
        
        logger.info(f"Publication created successfully - Publication ID: {publication.publication_id}")
        serializer = PublicationSerializer(publication, context={'request': request})
        return Response({"status": "success", "message": "Publication created", "data": serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error creating publication: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## Edit publications
@api_view(['PUT'])
@permission_classes([IsAuthenticatedCustom])
def edit_publication(request):

    """
    Edit publication.

    Request Body:
    {
        "publication_id": "integer",
        "publication_title": "string",
        "topic_id": "integer",
        "short_note": "string",
        "logo_image": "file",
        "topics_of_publications": "string",
        "default_article_visibility": "string"
    }
    """
    user = request.user

    publication_id = request.data.get('publication_id')
    get_publication_title = request.data.get('publication_title')
    get_topic_id = request.data.get('topic_id')
    get_short_note = request.data.get('short_note')
    get_logo_image = request.FILES.get('logo_image')
    get_topics_of_publications = request.data.get('topics_of_publications') # Enter topics id or topics name
    get_default_article_visibility = request.data.get('default_article_visibility','public')

    if not publication_id:
        logger.warning("Publication edit failed - publication_id is required")
        return Response({"status": "error", "message": "publication_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        logger.info(f"Editing publication - Publication ID: {publication_id} - User: {user.user_id}")
        publication = Publication.objects.get(publication_id = publication_id)

        editors = publication.editors.filter(user_id=user.user_id).exists()
        writers = publication.writers.filter(user_id=user.user_id).exists()

        if not (editors or writers or user == publication.owner):
            logger.warning(f"Permission denied for editing publication - Publication ID: {publication_id} - User: {user.user_id}")
            return Response({"status": "error", "message": "You do not have permission to update this publication"}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
 
            if get_publication_title is not None:
                publication.publication_title = get_publication_title

            if get_topic_id is not None:
                topic = Topics.objects.filter(topic_id = get_topic_id).first()
                publication.topic = topic

            if get_short_note is not None:
                publication.short_note = get_short_note

            if get_logo_image is not None:
                try:
                    validate_image(get_logo_image)
                except Exception as e:
                    logger.warning(f"Image validation failed: {str(e)}")
                    return Response({"status":"fail","message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
                publication.logo_image = get_logo_image

            if get_topics_of_publications is not None:
                publication.topics_of_publications = get_topics_of_publications

            if get_default_article_visibility is not None:
                publication.default_article_visibility = get_default_article_visibility

            publication.updated_at = timezone.now()
            publication.updated_by = user
            publication.save()

        logger.info(f"Publication updated successfully - Publication ID: {publication.publication_id}")
        serializer = PublicationSerializer(publication, context={'request': request})
        return Response({"status": "success", "message": "Publication updated", "data": serializer.data}, status=status.HTTP_200_OK)

    except Publication.DoesNotExist:
        logger.warning(f"Publication not found for editing - Publication ID: {publication_id}")
        return Response({"status": "error", "message": "publication not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error editing publication: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## Delete publication
@api_view(['DELETE'])
@permission_classes([IsAuthenticatedCustom])
def delete_publication(request):

    """
    Delete a publication.

    Request Body:
    {
        "publication_id": "integer"
    }
    """
    user = request.user

    try:
        publication_id = request.data.get('publication_id')

        if not publication_id:
            logger.warning("Publication deletion failed - publication_id is required")
            return Response({"status": "error", "message": "publication_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        publication = Publication.objects.get(publication_id = publication_id)
        editors = publication.editors.filter(user_id=getattr(request.user,'user_id', None)).exists()
        writers = publication.writers.filter(user_id=getattr(request.user,'user_id', None)).exists()

        if user != editors(publication) and user != writers(publication) and user != publication.owner:
            logger.warning(f"Permission denied for deleting publication - Publication ID: {publication_id} - User: {user.user_id}")
            return Response({"status": "error", "message": "You do not have permission to delete this publication"}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            publication = Publication.objects.get(publication_id = publication_id)
            publication.delete()
        
        logger.info(f"Publication deleted successfully - Publication ID: {publication_id}")
        return Response({"status": "success", "message": "Publication deleted"}, status=status.HTTP_200_OK)
    
    except Publication.DoesNotExist:
        logger.warning(f"Publication not found for deletion - Publication ID: {publication_id}")
        return Response({"status": "error", "message": "publication not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error deleting publication: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## view/Explore Publications
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def view_publications(request):
    """
    View all publications.

    Request Body:
    None
    """
    try:
        logger.info(f"Viewing all publications - User: {request.user.user_id}")
        publications = Publication.objects.all()
        serializer = PublicationSerializer(publications, many=True, context={'request': request})
        logger.info(f"Successfully fetched {len(publications)} publications")
        return Response({"status": "success", "message": "Publications found", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error viewing publications: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#################### STAFF PICKS APIs #####################

## add staf picks
@api_view(['POST'])
@permission_classes([IsAdminCustom])
def add_staff_picks(request):

    """
    Add an article to staff picks.

    Request Body:
    {
        "publication_id": "integer",
        "article_id": "integer",
        "topic_id": "integer"
    }
    """
    user = request.user

    publication_id = request.data.get('publication_id')
    article_id = request.data.get('article_id')
    topic_id = request.data.get('topic_id')

    if not publication_id or not article_id:
        logger.warning("Staff picks addition failed - publication_id and article_id are required")
        return Response({"status": "error", "message": "publication_id and article_id are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        logger.info(f"Adding staff pick - Publication ID: {publication_id}, Article ID: {article_id} - User: {user.user_id}")
        publication = Publication.objects.filter(publication_id = publication_id).first()
        article = Article.objects.filter(article_id = article_id).first()
        topic = Topics.objects.filter(topic_id = topic_id).first()

        with transaction.atomic():
            StaffPics.objects.create(
                                    publications = publication, 
                                    article = article, 
                                    topic = topic, 
                                    created_at = timezone.now(),
                                    created_by = user)
        
        logger.info(f"Staff pick added successfully - Publication ID: {publication_id}, Article ID: {article_id}")
        return Response({"status": "success", "message": "Article added to staff picks"}, status=status.HTTP_200_OK)

    except Publication.DoesNotExist:
        logger.warning(f"Publication not found for staff picks - Publication ID: {publication_id}")
        return Response({"status": "error", "message": "publication not found"}, status=status.HTTP_404_NOT_FOUND)

    except Article.DoesNotExist:
        logger.warning(f"Article not found for staff picks - Article ID: {article_id}")
        return Response({"status": "error", "message": "article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error adding staff pick: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## edit staff picks
@api_view(['PUT'])
@permission_classes([IsAdminCustom])
def edit_staff_picks(request):

    """
    Edit staff picks.

    Request Body:
    {
        "publication_id": "integer",
        "article_id": "integer",
        "topic_id": "integer"
    }
    """
    
    user = request.user
    publication_id = request.data.get('publication_id')
    article_id = request.data.get('article_id')
    topic_id = request.data.get('topic_id')

    if not publication_id or not article_id:
        logger.warning("Staff picks edit failed - publication_id and article_id are required")
        return Response({"status": "error", "message": "publication_id and article_id are required"},status=status.HTTP_400_BAD_REQUEST)

    try:
        logger.info(f"Editing staff pick - Publication ID: {publication_id}, Article ID: {article_id} - User: {user.user_id}")
        publication = Publication.objects.get(publication_id=publication_id)
        article = Article.objects.get(article_id=article_id)
        topic = Topics.objects.filter(topic_id=topic_id).first() if topic_id else None

        staff = StaffPics.objects.filter(publications=publication, article=article).first()
        if not staff:
            logger.warning(f"Staff pick record not found - Publication ID: {publication_id}, Article ID: {article_id}")
            return Response({"status": "error", "message": "Staff pick record not found"},status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():

            staff.publications = publication
            staff.article = article
            if topic:
                staff.topic = topic

            staff.updated_at = timezone.now()
            staff.updated_by = user
            staff.save()

        logger.info(f"Staff pick updated successfully - Staff Pick ID: {staff.staff_pic_id}")
        serializer = StaffPicsSerializer(staff, context={'request': request})
        return Response({"status": "success", "message": "Staff pick updated successfully", "updated_data": serializer.data},status=status.HTTP_200_OK)

    except Publication.DoesNotExist:
        logger.warning(f"Publication not found for staff picks edit - Publication ID: {publication_id}")
        return Response({"status": "error", "message": "Publication not found"}, status=status.HTTP_404_NOT_FOUND)

    except Article.DoesNotExist:
        logger.warning(f"Article not found for staff picks edit - Article ID: {article_id}")
        return Response({"status": "error", "message": "Article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error editing staff pick: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Remove from staff picks
@api_view(['PUT'])
@permission_classes([IsAdminCustom])
def remove_staff_pick_field(request):

    """
    Remove fields from staff picks.

    Request Body:
    {
        "staff_pic_id": "integer",
        "remove_article": "boolean",
        "remove_topic": "boolean",
        "remove_publication": "boolean"
    }
    """
    staff_pic_id = request.data.get('staff_pic_id')
    remove_article = request.data.get('article_id')
    remove_topic = request.data.get('topic_id')
    remove_publication = request.data.get('publication_id')

    if not staff_pic_id:
        logger.warning("Staff pick field removal failed - staff_pic_id is required")
        return Response({"status": "error", "message": "staff_pic_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        logger.info(f"Removing staff pick field - Staff Pick ID: {staff_pic_id} - User: {request.user.user_id}")
        staff_pick = StaffPics.objects.get(staff_pic_id=staff_pic_id)

        with transaction.atomic():
            if remove_article:
                staff_pick.article = None

            if remove_topic:
                staff_pick.topic = None

            if remove_publication:
                staff_pick.publications = None

            staff_pick.updated_at = timezone.now()
            staff_pick.updated_by = request.user
            staff_pick.save()

        logger.info(f"Staff pick field removed successfully - Staff Pick ID: {staff_pic_id}")
        return Response({"status": "success", "message": "Staff pick field removed successfully"}, status=status.HTTP_200_OK)

    except StaffPics.DoesNotExist:
        logger.warning(f"Staff pick not found for field removal - Staff Pick ID: {staff_pic_id}")
        return Response({"status": "error", "message": "Staff pick not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error removing staff pick field: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## view all staff picks articles 
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def view_all_staff_picks(request):

    """
    View all staff picks articles

    Request Body:
    {
        "publication_id": "integer",
        "article_id": "integer",
        "topic_id": "integer"
    }
    """
    publication_id = request.data.get('publication_id')
    article_id = request.data.get('article_id')
    topic_id = request.data.get('topic_id')

    try:
        logger.info(f"Viewing all staff picks - User: {request.user.user_id}")
        staff_picks = StaffPics.objects.all()

        if publication_id:
            staff_picks = staff_picks.filter(publications__publication_id=publication_id)

        if article_id:
            staff_picks = staff_picks.filter(article__article_id=article_id)

        if topic_id:
            staff_picks = staff_picks.filter(topic__topic_id=topic_id)

        #response data
        response_data = []
        for sp in staff_picks:
            response_data.append({
                "staff_pic_id": sp.staff_pic_id,
                "article_id": sp.article.article_id,
                "article_title": sp.article.article_title,
                "topic_id": sp.topic.topic_id if sp.topic else None,
                "topic_name": sp.topic.topic_name if sp.topic else None,
                "publication_id": sp.publications.publication_id if sp.publications else None,
                "publication_name": sp.publications.publication_name if sp.publications else None,
                "total_stories": float(sp.total_stories),
                "total_saves": float(sp.total_saves),
                "created_at": sp.created_at,
                "updated_at": sp.updated_at,
                "created_by": sp.created_by.username if sp.created_by else None,
                "updated_by": sp.updated_by.username if sp.updated_by else None
            })

        logger.info(f"Successfully fetched {len(response_data)} staff picks")
        return Response({"status": "success", "message": "staff_picks fetched successfully", "data": response_data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error viewing staff picks: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## Follow Publications
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def follow_publication(request):

    """
    Follow a publication.

    Request Body:
    {
        "publication_id": "integer",
        "mark_publications_followed": "string"
    }
    """
    user = request.user
    get_publication_id = request.data.get('publication_id')
    mark_publications_followed = request.data.get('mark_publications_followed')

    if not get_publication_id: 
        logger.warning("Publication follow failed - publication_id is required")
        return Response({"status": "error", "message": "publication_id is required"},status=status.HTTP_400_BAD_REQUEST)

    try:
        logger.info(f"Following publication - Publication ID: {get_publication_id} - User: {user.user_id}")
        publication = Publication.objects.get(publication_id=get_publication_id)

        if publication.followers.filter(user_id=user.user_id).exists():
            logger.warning(f"User already following publication - Publication ID: {get_publication_id} - User: {user.user_id}")
            return Response({"status": "fail", "message": "Already following this publication"},status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if mark_publications_followed == 'true' or mark_publications_followed == 'True':
                publication.followers.add(user)
                user.is_following_publications = True
                user.save(update_fields=['is_following_publications'])

        logger.info(f"User successfully followed publication - Publication ID: {get_publication_id} - User: {user.user_id}")
        return Response({"status": "success", "message": f"You are now following '{publication.publication_title}'"},status=status.HTTP_200_OK)

    except Publication.DoesNotExist:
        logger.warning(f"Publication not found for following - Publication ID: {get_publication_id}")
        return Response({"status": "error", "message": "Publication not found"},status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error following publication: {str(e)}")
        return Response({"status": "error", "message": str(e)},status=status.HTTP_400_BAD_REQUEST)
    
## Unfollow Publications
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def unfollow_publication(request):

    """
    Unfollow a publication.

    Request Body:
    {
        "publication_id": "integer",
        "mark_publications_unfollow": "string"
    }
    """
    user = request.user
    get_publication_id = request.data.get('publication_id')
    mark_publications_unfollow = request.data.get('mark_publications_unfollow')

    if not get_publication_id:
        logger.warning("Publication unfollow failed - publication_id is required")
        return Response({"status": "error", "message": "publication_id is required"},status=status.HTTP_400_BAD_REQUEST)

    try:
        logger.info(f"Unfollowing publication - Publication ID: {get_publication_id} - User: {user.user_id}")
        publication = Publication.objects.get(publication_id = get_publication_id)
        
        if not publication.followers.filter(user_id=user.user_id).exists():
            logger.warning(f"User not following publication for unfollow - Publication ID: {get_publication_id} - User: {user.user_id}")
            return Response({"status": "fail", "message": "You are not following this publication"},status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if mark_publications_unfollow == 'true' or mark_publications_unfollow == 'True':
                publication.followers.remove(user)
                user.is_following_publications = False
                user.save(update_fields=['is_following_publications'])

        logger.info(f"User successfully unfollowed publication - Publication ID: {get_publication_id} - User: {user.user_id}")
        return Response({"status": "success", "message": f"You unfollowed '{publication.publication_title}'"},status=status.HTTP_200_OK)

    except Publication.DoesNotExist:
        logger.warning(f"Publication not found for unfollowing - Publication ID: {get_publication_id}")
        return Response({"status": "error", "message": "Publication not found"},status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error unfollowing publication: {str(e)}")
        return Response({"status": "error", "message": str(e)},status=status.HTTP_400_BAD_REQUEST)
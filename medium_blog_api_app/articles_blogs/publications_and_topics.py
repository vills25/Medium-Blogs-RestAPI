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

#################### TOPICS #####################
## Create topics
@api_view(['POST'])
@permission_classes([IsAdminCustom])
def create_topic(request):
    try:
        header1 = request.data.get('topic_header_1')
        if not header1:
            return Response({"status": "error", "message": "topic_header_1 is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        header2 = request.data.get('topic_header_2', '')
        header3 = request.data.get('topic_header_3', '')
        desc = request.data.get('topic_description', '')
        with transaction.atomic():
            topic = Topics.objects.create(
                topic_header_1=header1,
                topic_header_2=header2,
                topic_header_3=header3,
                topic_description=desc,
                created_by=request.user,
                updated_by=request.user
            )
        serializer = TopicsSerializer(topic, context={'request': request})
        return Response({"status": "success", "message": "Topic created", "data": serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Edit topics
@api_view(['PUT'])
@permission_classes([IsAdminCustom])
def edit_topic(request):
    try:
        topic_id = request.data.get('topic_id')
        header1 = request.data.get('topic_header_1')
        header2 = request.data.get('topic_header_2', '')
        header3 = request.data.get('topic_header_3', '')
        topic_description = request.data.get('topic_description', '')

        if not topic_id:
            return Response({"status": "error", "message": "topic_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        topic = Topics.objects.get(topic_id = topic_id)

        with transaction.atomic():
            topic.topic_header_1 = header1
            topic.topic_header_2 = header2
            topic.topic_header_3 = header3
            topic.topic_description = topic_description
            topic.updated_by = request.user
            topic.save()
        serializer = TopicsSerializer(topic, context={'request': request})
        return Response({"status": "success", "message": "Topic updated", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except Topics.DoesNotExist:
            return Response({"status": "error", "message": "topic not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## Delete topics
@api_view(['DELETE'])
@permission_classes([IsAdminCustom])
def delete_topic(request):
    try:
        topic_id = request.data.get('topic_id')

        if not topic_id:
            return Response({"status": "error", "message": "topic_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            topic = Topics.objects.get(topic_id = topic_id)

            topic.delete()
        return Response({"status": "success", "message": "Topic deleted"}, status=status.HTTP_200_OK)
    
    except Topics.DoesNotExist:
            return Response({"status": "error", "message": "topic not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## view all topics
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def view_all_topics(request):
    try:
        topics = Topics.objects.all()
        serializer = TopicsSerializer(topics, many=True, context={'request': request})
        return Response({"status": "success", "message": "Topics fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## search topics
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def search_topics(request):

    search_topic = request.data.get('enter_text')
    if not search_topic:
        return Response({"status": "error", "message": "enter_text is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:

        topics = Topics.objects.filter(Q(topic_header_1__icontains=search_topic) | 
                                       Q(topic_header_2__icontains=search_topic) | 
                                       Q(topic_header_3__icontains=search_topic) | 
                                       Q(topic_description__icontains=search_topic))

        serializer = TopicsSerializer(topics, many=True, context={'request': request})
        return Response({"status": "success", "message": "Topics fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#################### PUBLICATION #####################
## Create publications
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def create_publication(request):
    try:
        get_publication_title = request.data.get('publication_title')
        get_topic_id = request.data.get('topic_id')
        get_short_note = request.data.get('short_note')
        get_logo_image = request.FILES.get('logo_image')
        get_topics_of_publications = request.data.get('topics_of_publications') # Enter topics id or topics name
        get_default_article_visibility = request.data.get('default_article_visibility','public')
        if not get_publication_title:
            return Response({"status": "error", "message": "publication_name is required"}, status=status.HTTP_400_BAD_REQUEST)

        topic = None
        if get_topic_id:
            topic = Topics.objects.filter(topic_id = get_topic_id).first()

        if get_logo_image:
            try:
                validate_image(get_logo_image)
            except Exception as e:
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
        serializer = PublicationSerializer(publication, context={'request': request})
        return Response({"status": "success", "message": "Publication created", "data": serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## Edit publications
@api_view(['PUT'])
@permission_classes([IsAuthenticatedCustom])
def edit_publication(request):

    user = request.user

    publication_id = request.data.get('publication_id')
    get_publication_title = request.data.get('publication_title')
    get_topic_id = request.data.get('topic_id')
    get_short_note = request.data.get('short_note')
    get_logo_image = request.FILES.get('logo_image')
    get_topics_of_publications = request.data.get('topics_of_publications') # Enter topics id or topics name
    get_default_article_visibility = request.data.get('default_article_visibility','public')

    if not publication_id:
        return Response({"status": "error", "message": "publication_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:

        publication = Publication.objects.get(publication_id = publication_id)
        # editors = publication.editors.filter(user_id=getattr(request.user,'user_id', None)).exists()
        # writers = publication.writers.filter(user_id=getattr(request.user,'user_id', None)).exists()

        editors = publication.editors.filter(user_id=user.user_id).exists()
        writers = publication.writers.filter(user_id=user.user_id).exists()

        if not (editors or writers or user == publication.owner):
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
                    return Response({"status":"fail","message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
                publication.logo_image = get_logo_image

            if get_topics_of_publications is not None:
                publication.topics_of_publications = get_topics_of_publications

            if get_default_article_visibility is not None:
                publication.default_article_visibility = get_default_article_visibility

            publication.updated_at = timezone.now()
            publication.updated_by = user
            publication.save()

        serializer = PublicationSerializer(publication, context={'request': request})
        return Response({"status": "success", "message": "Publication updated", "data": serializer.data}, status=status.HTTP_200_OK)

    except Publication.DoesNotExist:
            return Response({"status": "error", "message": "publication not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## Delete publication
@api_view(['DELETE'])
@permission_classes([IsAuthenticatedCustom])
def delete_publication(request):

    user = request.user

    try:
        publication_id = request.data.get('publication_id')

        if not publication_id:
            return Response({"status": "error", "message": "publication_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        publication = Publication.objects.get(publication_id = publication_id)
        editors = publication.editors.filter(user_id=getattr(request.user,'user_id', None)).exists()
        writers = publication.writers.filter(user_id=getattr(request.user,'user_id', None)).exists()

        if user != editors(publication) and user != writers(publication) and user != publication.owner:
            return Response({"status": "error", "message": "You do not have permission to delete this publication"}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            publication = Publication.objects.get(publication_id = publication_id)

            publication.delete()
        return Response({"status": "success", "message": "Publication deleted"}, status=status.HTTP_200_OK)
    
    except Publication.DoesNotExist:
            return Response({"status": "error", "message": "publication not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## view/Explore Publications
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def view_publications(request):
    try:
        publications = Publication.objects.all()
        serializer = PublicationSerializer(publications, many=True, context={'request': request})
        return Response({"status": "success", "message": "Publications found", "data": serializer.data}, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#################### STAFF PICKS APIs #####################

## add staf picks
@api_view(['POST'])
@permission_classes([IsAdminCustom])
def add_staff_picks(request):

    user = request.user

    publication_id = request.data.get('publication_id')
    article_id = request.data.get('article_id')
    topic_id = request.data.get('topic_id')

    if not publication_id or not article_id:
        return Response({"status": "error", "message": "publication_id and article_id are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:    
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
            return Response({"status": "success", "message": "Article added to staff picks"}, status=status.HTTP_200_OK)

    except Publication.DoesNotExist:
            return Response({"status": "error", "message": "publication not found"}, status=status.HTTP_404_NOT_FOUND)

    except Article.DoesNotExist:
            return Response({"status": "error", "message": "article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## edit staff picks
@api_view(['PUT'])
@permission_classes([IsAdminCustom])
def edit_staff_picks(request):

    user = request.user
    publication_id = request.data.get('publication_id')
    article_id = request.data.get('article_id')
    topic_id = request.data.get('topic_id')

    if not publication_id or not article_id:
        return Response({"status": "error", "message": "publication_id and article_id are required"},status=status.HTTP_400_BAD_REQUEST)

    try:
        publication = Publication.objects.get(publication_id=publication_id)
        article = Article.objects.get(article_id=article_id)
        topic = Topics.objects.filter(topic_id=topic_id).first() if topic_id else None

        staff = StaffPics.objects.filter(publications=publication, article=article).first()
        if not staff:
            return Response({"status": "error", "message": "Staff pick record not found"},status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():

            staff.publications = publication
            staff.article = article
            if topic:
                staff.topic = topic

            staff.updated_at = timezone.now()
            staff.updated_by = user
            staff.save()

        serializer = StaffPicsSerializer(staff, context={'request': request})
        return Response({"status": "success", "message": "Staff pick updated successfully", "updated_data": serializer.data},status=status.HTTP_200_OK)

    except Publication.DoesNotExist:
        return Response({"status": "error", "message": "Publication not found"}, status=status.HTTP_404_NOT_FOUND)

    except Article.DoesNotExist:
        return Response({"status": "error", "message": "Article not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

## Remove from staff picks
@api_view(['PUT'])
@permission_classes([IsAdminCustom])
def remove_staff_pick_field(request):

    staff_pic_id = request.data.get('staff_pic_id')
    remove_article = request.data.get('article_id')
    remove_topic = request.data.get('topic_id')
    remove_publication = request.data.get('publication_id')

    if not staff_pic_id:
        return Response({"status": "error", "message": "staff_pic_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
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

        return Response({"status": "success", "message": "Staff pick field removed successfully"}, status=status.HTTP_200_OK)

    except StaffPics.DoesNotExist:
        return Response({"status": "error", "message": "Staff pick not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


## view all staff picks articles 
@api_view(['GET'])
@permission_classes([IsAuthenticatedCustom])
def view_all_staff_picks(request):

    publication_id = request.data.get('publication_id')
    article_id = request.data.get('article_id')
    topic_id = request.data.get('topic_id')

    try:
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

        return Response({"status": "success", "message": "staff_picks fetched successfully", "data": response_data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
## Follow Publications
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def follow_publication(request):

    user = request.user
    get_publication_id = request.data.get('publication_id')
    mark_publications_followed = request.data.get('mark_publications_followed')

    if not get_publication_id: 
        return Response({"status": "error", "message": "publication_id is required"},status=status.HTTP_400_BAD_REQUEST)

    try:

        publication = Publication.objects.get(publication_id=get_publication_id)

        if publication.followers.filter(user_id=user.user_id).exists():
            return Response({"status": "fail", "message": "Already following this publication"},status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if mark_publications_followed == 'true' or mark_publications_followed == 'True':
                publication.followers.add(user)
                user.is_following_publications = True
                user.save(update_fields=['is_following_publications'])

        return Response({"status": "success", "message": f"You are now following '{publication.publication_title}'"},status=status.HTTP_200_OK)

    except Publication.DoesNotExist:
            return Response({"status": "error", "message": "Publication not found"},status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status": "error", "message": str(e)},status=status.HTTP_400_BAD_REQUEST)
    
## Unfollow Publications
@api_view(['POST'])
@permission_classes([IsAuthenticatedCustom])
def unfollow_publication(request):

    user = request.user
    get_publication_id = request.data.get('publication_id')
    mark_publications_unfollow = request.data.get('mark_publications_unfollow')

    if not get_publication_id:
        return Response({"status": "error", "message": "publication_id is required"},status=status.HTTP_400_BAD_REQUEST)

    try:
        publication = Publication.objects.get(publication_id=get_publication_id)
        
        if not publication.followers.filter(user_id=user.user_id).exists():
            return Response({"status": "fail", "message": "You are not following this publication"},status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if mark_publications_unfollow == 'true' or mark_publications_unfollow == 'True':
                publication.followers.remove(user)
                user.is_following_publications = False
                user.save(update_fields=['is_following_publications'])

        return Response({"status": "success", "message": f"You unfollowed '{publication.publication_title}'"},status=status.HTTP_200_OK)

    except Publication.DoesNotExist:
        return Response({"status": "error", "message": "Publication not found"},status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"status": "error", "message": str(e)},status=status.HTTP_400_BAD_REQUEST)
    

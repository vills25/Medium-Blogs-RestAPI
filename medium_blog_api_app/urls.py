from django.urls import path
from medium_blog_api_app.articles_blogs.readinglist import *
from medium_blog_api_app.user.user_view import *
from medium_blog_api_app.articles_blogs.articles_view import *
from medium_blog_api_app.articles_blogs.clap_and_comments import *
from medium_blog_api_app.articles_blogs.publications_and_topics import *

urlpatterns = [

    #-------- AUTHENTICATION & USER --------#
    path('register/', register_user),
    path('login/', login_user),
    path('logout/', logout_user),
    path('edit-profile/', edit_profile),
    path('delete-profile/', delete_profile),
    path('deactivate-profile/', deactivate_profile),
    path('change-password/', change_password),
    path('forgot-password/', forgot_password),
    path('reset-password/', reset_password),
    path('follow-user/', follow_user),
    path('unfollow-user/', unfollow_user),
    path('view_my_profile/', view_my_profile),
    path('get-any-users/', view_other_user_profile),
    path('get-my-following-list/', view_my_following_list),

    #-------- ARTICLES --------#
    path('new-story/', create_article),
    path('update-article/', update_article),
    path('delete-article/', delete_article),
    path('search-articles/', search_articles),
    path('get_all_articles/', get_all_articles),
    path('report-articles/', report_article),
    path('get-reported-articles/', get_reported_articles),
    path('get-my-articles/', get_my_articles),
    path('share-article/', share_article),
    path('undo-reshare/',undo_reshare),
    path('shared-articles/', get_shared_articles),
    path('mute-author/', mute_author),
    path('mute-publication/', mute_publication),
    path('show-less/', show_less_like_this_func),
    
    #-------- TOPICS --------#
    path('create-topic/', create_topic),
    path('edit-topic/', edit_topic),
    path('delete-topic/', delete_topic),
    path('view-all-topics/', view_all_topics),
    path('search-topics/', search_topics),

    #-------- PUBLICATIONS --------#
    path('create-publication/', create_publication),
    path('edit-publication/', edit_publication),
    path('delete-publication/', delete_publication),
    path('view-publication/', view_publications),
    path('follow-publication/', follow_publication),
    path('unfollow-publication/', unfollow_publication),

    #-------- STAFS PICK --------#
    path('add-to-staff-picks/', add_staff_picks),
    path('edit-staff-picks/', edit_staff_picks),
    path('remove-staff-pick-field/', remove_staff_pick_field),
    path('view-all-staff-picks/', view_all_staff_picks),

    #-------- CLAPS --------#
    path('give-clap/', give_clap),
    path('remove-clap/', remove_clap),

    #-------- COMMENTS --------#
    path('create-comment/', add_comment),
    path('edit-comment/', edit_comment),
    path('delete-comment/', remove_comment),

    #-------- LISTS --------#
    path('create-readinglist/', create_readinglist),
    path('get-readinglist/', get_readinglist),
    path('delete-readinglist/', delete_readinglist),
    path('edit-readinglist/', edit_readinglist),
    path('add-multiple-to-readinglist/', add_multiple_to_readinglist),
    path('clear-readinglist/', clear_readinglist),
    path('search-readinglist/', search_readinglist),
    path('get-readinglist-stats/', get_readinglist_stats),

]
from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,
    UserPostListView
)
from . import views

urlpatterns = [
    #path('', views.forum, name ='feed-forum'),
    path('', PostListView.as_view(), name ='feed-forum'),
    path('user/<str:username>', UserPostListView.as_view(), name='user-posts'),
    path('post/<int:pk>/', PostDetailView.as_view(), name ='post-detail'),
    #path('post/<int:pk>/', views.postDetailView, name ='post-detail'),
    path('post/new/', PostCreateView.as_view(), name ='post-create'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    #path('survey/', views.survey_question, name ='feed-survey'),
    path('stat/', views.mentee_stat, name ='feed-stat'),
    path('get_generated_response/', views.generate_respose_with_AI, name='get_text'),
]
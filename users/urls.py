# users/urls.py

from django.urls import path
from .views import (
    UserRegistrationView, 
    UserLoginView, 
    UserSearchView, 
    UserActivityView, 
    UserListView, 
    UserDetailView,
    BlockUserView, 
    UnblockUserView
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('search/', UserSearchView.as_view(), name='user-search'),
    path('activity/', UserActivityView.as_view(), name='user-activity'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('block/', BlockUserView.as_view(), name='block-user'),  
    path('unblock/', UnblockUserView.as_view(), name='unblock-user'),
]

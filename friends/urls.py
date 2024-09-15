# friends/urls.py

from django.urls import path
from .views import *

urlpatterns = [
    path('request/', FriendRequestView.as_view(), name='friend-request'),
    path('request/<int:id>/action/', FriendRequestActionView.as_view(), name='friend-request-action'),
    path('list/', FriendListView.as_view(), name='friend-list'),
    path('pending/', PendingFriendRequestsView.as_view(), name='pending-friend-requests'),

]
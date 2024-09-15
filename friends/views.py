from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from django.db.models import Q
from .models import Friend
from users.models import UserBlock
from .serializers import FriendSerializer, FriendRequestSerializer
from rest_framework.throttling import UserRateThrottle
from datetime import timedelta
from django.db import transaction
from django.core.cache import cache
from users.views import log_user_activity
from users.permissions import IsWriter


class FriendRequestThrottle(UserRateThrottle):
    """Custom rate throttle class to limit friend requests to 3 per minute."""
    rate = '3/minute'


class FriendRequestView(generics.CreateAPIView):
    """
    API view to send a friend request to another user.

    - Throttles friend requests to 3 per minute.
    - Checks if the receiver has blocked the sender.
    - Implements a cooldown period (24 hours) if a previous request was rejected.
    - Logs the activity of sending a friend request.
    """
    authentication_classes = (TokenAuthentication, SessionAuthentication, JWTAuthentication)
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated, IsWriter]  # Writers and Admins can send friend requests
    throttle_classes = [FriendRequestThrottle]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Creates a friend request.

        - Ensures that the receiver has not blocked the sender.
        - Checks if the sender is within the cooldown period if the request was previously rejected.
        - If a valid request, logs the activity and returns the friend request data.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receiver = serializer.validated_data['receiver']

        # Check if the receiver has blocked the sender
        if UserBlock.objects.filter(blocker=receiver, blocked=request.user).exists():
            return Response({'error': 'You cannot send a friend request to this user.'}, status=status.HTTP_403_FORBIDDEN)

        # Check cooldown period
        cooldown_period = timedelta(hours=24)
        last_request = Friend.objects.filter(
            sender=request.user,
            receiver=receiver,
            status='rejected',
            updated_at__gte=timezone.now() - cooldown_period
        ).first()

        if last_request:
            return Response({'error': 'You cannot send another request to this user yet.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Create or retrieve the friend request
        with transaction.atomic():
            friend_request, created = Friend.objects.get_or_create(
                sender=request.user,
                receiver=receiver,
                defaults={'status': 'pending'}
            )
            if not created:
                return Response({'error': 'Friend request already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Log the friend request activity
        log_user_activity(request.user, 'FRIEND_REQUEST_SENT', {'receiver_id': receiver.id})
        return Response(FriendSerializer(friend_request).data, status=status.HTTP_201_CREATED)



class FriendRequestActionView(generics.UpdateAPIView):
    """
    API view to accept or reject a friend request.

    - Only allows the receiver of the friend request to perform actions.
    - Supports two actions: 'accept' and 'reject'.
    - Logs the friend request action.
    """
    authentication_classes = (TokenAuthentication, SessionAuthentication, JWTAuthentication)
    serializer_class = FriendSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        """Retrieve only pending friend requests where the current user is the receiver."""
        return Friend.objects.filter(receiver=self.request.user, status='pending')

    def update(self, request, *args, **kwargs):
        """
        Accepts or rejects a friend request based on the provided action.

        - Updates the request's status to 'accepted' or 'rejected'.
        - Logs the action (either 'FRIEND_REQUEST_ACCEPTED' or 'FRIEND_REQUEST_REJECTED').
        """
        instance = self.get_object()
        action = request.data.get('action')
        if action not in ['accept', 'reject']:
            return Response({'error': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            instance.status = 'accepted' if action == 'accept' else 'rejected'
            instance.save()

        # Log the friend request action
        log_user_activity(request.user, f'FRIEND_REQUEST_{action.upper()}', {'sender_id': instance.sender.id})
        return Response(self.get_serializer(instance).data)


class FriendListView(generics.ListAPIView):
    """
    API view to list all accepted friends of the current user.

    - Uses caching to store the result for 5 minutes to optimize performance.
    """
    authentication_classes = (TokenAuthentication, SessionAuthentication, JWTAuthentication)
    serializer_class = FriendSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves the list of accepted friends for the current user.

        - Caches the queryset to reduce repeated queries within a 5-minute window.
        """
        cache_key = f'friend_list_{self.request.user.id}'
        queryset = cache.get(cache_key)
        if queryset is None:
            queryset = Friend.objects.filter(
                (Q(sender=self.request.user) | Q(receiver=self.request.user)) & Q(status='accepted')
            ).select_related('sender', 'receiver')
            cache.set(cache_key, queryset, timeout=300)  # Cache for 5 minutes
        return queryset


class PendingFriendRequestsView(generics.ListAPIView):
    """
    API view to list all pending friend requests for the current user.

    - Displays all requests where the user is the receiver, and the status is 'pending'.
    """
    authentication_classes = (TokenAuthentication, SessionAuthentication, JWTAuthentication)
    serializer_class = FriendSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve all pending friend requests for the current user."""
        return Friend.objects.filter(receiver=self.request.user, status='pending').select_related('sender')

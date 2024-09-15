from django.shortcuts import render
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, 
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserActivitySerializer
)
from .permissions import IsAdmin, IsWriter, IsReader
from .models import UserBlock, UserActivity

# Utility function to log user activity
def log_user_activity(user, activity_type, details):
    """Log user activities for tracking purposes."""
    UserActivity.objects.create(user=user, activity_type=activity_type, details=details)

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    """
    API view to register a new user.
    
    - Allows any user to register.
    - Returns JWT tokens on successful registration.
    - Logs the registration activity.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Handle user registration and return JWT tokens."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        log_user_activity(user, 'REGISTRATION', {'method': 'email'})
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    """
    API view for user login.
    
    - Allows any user to login with email and password.
    - Returns JWT tokens on successful login.
    - Logs the login activity.
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Handle user login and return JWT tokens if credentials are valid."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data['email']).first()
        if user and user.check_password(serializer.validated_data['password']):
            refresh = RefreshToken.for_user(user)
            log_user_activity(user, 'LOGIN', {'method': 'email'})
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class UserSearchView(generics.ListAPIView):
    """
    API view to search for users by name or email.
    
    - Only authenticated users can perform the search.
    - Users can search by email or name.
    - Blocked users are pre-fetched to prevent showing them in the search results.
    """
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['email', 'name']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return a queryset of users, excluding blocked users."""
        queryset = User.objects.all().prefetch_related(
            Prefetch('blocking', queryset=UserBlock.objects.filter(blocker=self.request.user), to_attr='blocked_users')
        )
        search = self.request.query_params.get('search', None)
        if search:
            if '@' in search:
                return queryset.filter(email__iexact=search)
            return queryset.filter(name__icontains=search)
        return queryset


class UserListView(generics.ListAPIView):
    """
    API view to list all users.

    - Only users with 'read' permission or higher can access this view.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsReader]  # Readers, Writers, and Admins can access this view



class UserActivityView(generics.ListAPIView):
    """
    API view to retrieve the current user's activity log.

    - Only authenticated users can view their own activity.
    """
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated, IsReader]  # Readers, Writers, and Admins can view activity logs

    def get_queryset(self):
        """Return the activity log of the current authenticated user."""
        return UserActivity.objects.filter(user=self.request.user)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a user's information.

    - Admin users can access this view for full CRUD operations.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]  # Only Admins can access this view



class BlockUserView(generics.CreateAPIView):
    """
    API view to block a user.

    - Users with 'write' permission or higher can block other users.
    """
    permission_classes = [IsAuthenticated, IsWriter]  # Writers and Admins can block users

    def create(self, request, *args, **kwargs):
        """Block a user by adding a UserBlock instance."""
        blocker = request.user
        blocked = request.data.get('blocked_user')
        if blocker.id == blocked:
            return Response({'error': 'You cannot block yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        UserBlock.objects.create(blocker=blocker, blocked_id=blocked)
        log_user_activity(blocker, 'BLOCK_USER', {'blocked_user': blocked})
        return Response({'message': 'User blocked successfully.'}, status=status.HTTP_201_CREATED)


class UnblockUserView(generics.DestroyAPIView):
    """
    API view to unblock a user.
    
    - Users with 'write' permission or higher can unblock users.
    """
    permission_classes = [IsWriter]

    def delete(self, request, *args, **kwargs):
        """Unblock a user by deleting the UserBlock instance."""
        blocker = request.user
        blocked = request.data.get('blocked_user')
        UserBlock.objects.filter(blocker=blocker, blocked_id=blocked).delete()
        log_user_activity(blocker, 'UNBLOCK_USER', {'blocked_user': blocked})
        return Response({'message': 'User unblocked successfully.'}, status=status.HTTP_200_OK)

# friends/serializers.py

from rest_framework import serializers
from .models import Friend
from users.serializers import UserSerializer

class FriendSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Friend
        fields = ['id', 'sender', 'receiver', 'status', 'created_at', 'updated_at']

class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friend
        fields = ['receiver']
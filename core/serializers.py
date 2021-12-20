from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer
from store import serializers


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = ["id", "username", "password", "email", "first_name", "last_name"]


class SimpleUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ["id", "username", "email", "first_name", "last_name"]

from rest_framework import serializers
from .models import User, Contest, Task


class UserSerializer(serializers.ModelSerializer):
    date_joined = serializers.ReadOnlyField()

    class Meta(object):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'date_joined', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class ContestSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Contest
        fields = ('id', 'name', 'start_at', 'duration')


class TaskSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Task
        fields = ('id', 'header', 'body', 'efforts_available', 'picture')

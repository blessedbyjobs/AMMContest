from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_200_OK,
    HTTP_201_CREATED
)
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
import jwt
from rest_framework_jwt import *
from django.utils import timezone
from .serializers import UserSerializer, ContestSerializer
from .models import User, Contest
from Olympiada.settings import SECRET_KEY
from django.contrib.auth.signals import user_logged_in
from rest_framework_jwt.utils import jwt_payload_handler
from .permissions import IsAdminOrSelf


class CreateUserAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = (SessionAuthentication, BasicAuthentication)

    def post(self, request):
        user = request.data
        serializer = UserSerializer(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_201_CREATED)


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    # Allow only authenticated users to access this url
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        # serializer to handle turning our `User` object into something that
        # can be JSONified and sent to the client.
        serializer = self.serializer_class(request.user)

        return Response(serializer.data, status=HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        serializer_data = request.data.get('user', {})

        serializer = UserSerializer(
            request.user, data=serializer_data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny, ])
def authenticate_user(request):
    try:
        email = request.data['email']
        password = request.data['password']

        user = User.objects.get(email=email, password=password)
        if user:
            try:
                payload = jwt_payload_handler(user)
                token = jwt.encode(payload, SECRET_KEY)
                user_details = {}
                user_details['name'] = "%s %s" % (
                    user.first_name, user.last_name)
                user_details['token'] = token
                user_logged_in.send(sender=user.__class__,
                                    request=request, user=user)
                return Response(user_details, status=HTTP_200_OK)

            except Exception as e:
                raise e
        else:
            res = {
                'error': 'can not authenticate with the given credentials or the account has been deactivated'}
            return Response(res, status=HTTP_403_FORBIDDEN)
    except KeyError:
        res = {'error': 'please provide a email and a password'}
        return Response(res)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_all_contests(request):
    contests = Contest.objects.order_by('start_at')
    data = []

    for x in contests:
        if x.is_active:
            if x.duration.timestamp() > timezone.now().timestamp():
                contest = {}
                serializer = ContestSerializer(x, many=False)
                contest['id'] = serializer.data['id']
                contest['name'] = serializer.data['name']
                contest['start_at'] = serializer.data['start_at']
                contest['duration'] = serializer.data['duration']
                data.append(contest)
    return Response(data, status=HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_contest(request, contest_id):
    contests = Contest.objects.get(id=contest_id)
    contest = {}

    if contests.is_active:
        if contests.duration.timestamp() > timezone.now().timestamp():
            serializer = ContestSerializer(contests, many=False)
            contest['id'] = serializer.data['id']
            contest['name'] = serializer.data['name']
            contest['start_at'] = serializer.data['start_at']
            contest['duration'] = serializer.data['duration']
    return Response(contest, status=HTTP_200_OK)

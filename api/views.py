from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_404_NOT_FOUND
)
from rest_framework import viewsets
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
import jwt
from rest_framework_jwt import *
from django.utils import timezone
from .serializers import UserSerializer, ContestSerializer, TaskSerializer
from .models import User, Contest, Participate, is_participated, Task, Efforts, Example
from Olympiada.settings import SECRET_KEY
from django.contrib.auth.signals import user_logged_in
from rest_framework_jwt.utils import jwt_payload_handler
from .permissions import IsAdminOrSelf
from django.core.exceptions import ObjectDoesNotExist


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
    return JsonResponse(data, safe=False, status=HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_contest(request, contest_id):
    try:
        contests = Contest.objects.get(id=contest_id)
        contest = {}

        if contests.is_active:
            if contests.duration.timestamp() > timezone.now().timestamp():
                serializer = ContestSerializer(contests, many=False)
                contest['id'] = serializer.data['id']
                contest['name'] = serializer.data['name']
                contest['start_at'] = serializer.data['start_at']
                contest['duration'] = serializer.data['duration']
        return JsonResponse(contest, safe=False, status=HTTP_200_OK)
    except ObjectDoesNotExist:
        return JsonResponse([], safe=False)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def participate(request, contest_id):
    try:
        contest = Contest.objects.get(id=contest_id)

        if is_participated(user=request.user, contest=contest):
            return Response(status=HTTP_202_ACCEPTED)
        else:
            Participate.objects.create(user_id=request.user, contest_id=contest)
            return Response(status=HTTP_200_OK)
    except ObjectDoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_tasks(request, contest_id):
    tasks = Task.objects.filter(contest=contest_id)
    all_tasks = []

    for x in tasks:
        task = {}
        serializer = TaskSerializer(x, many=False)
        task['id'] = serializer.data['id']
        task['header'] = serializer.data['header']
        task['body'] = serializer.data['body']
        task['efforts_available'] = serializer.data['efforts_available']
        task['picture'] = serializer.data['picture']
        all_tasks.append(task)
    return JsonResponse(all_tasks, content_type="application/json", safe=False)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_task(request, contest_id, task_id):
    tasks = Task.objects.filter(contest=contest_id).get(id=task_id)

    task = {}
    serializer = TaskSerializer(tasks, many=False)
    task['id'] = serializer.data['id']
    task['header'] = serializer.data['header']
    task['body'] = serializer.data['body']
    task['efforts_available'] = serializer.data['efforts_available']
    task['picture'] = serializer.data['picture']

    return JsonResponse(task, safe=False, status=HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def send(request, contest_id, task_id):
    try:
        task = Task.objects.filter(contest=contest_id).get(id=task_id)
        effort = Efforts.objects.filter(user_id=request.user.id, task_id=task_id)

        if effort.count() <= task.efforts_available:
            tests = Example.objects.filter(task=task)
            for test in tests:
                if test.testing(input_data=request.data['solution']):
                    Efforts.objects.create(
                        user_id=request.user,
                        task_id=task,
                        solution=request.data['solution'],
                        solution_status=1,
                        test_passed=effort.count() + 1,
                        tests_count=task.efforts_available
                    )
                else:
                    Efforts.objects.create(
                        user_id=request.user,
                        task_id=task,
                        solution=request.solution,
                        solution_status=0,
                        test_passed=effort.count(),
                        tests_count=task.efforts_available
                    )
            json = {
                "message": "Решение принято"
            }
            return JsonResponse(json, safe=False, status=HTTP_202_ACCEPTED)
        else:
            json = {
                "message": "Превышено максимальное число попыток"
            }
            return JsonResponse(json, safe=False, status=HTTP_202_ACCEPTED)
    except ObjectDoesNotExist:
        json = {
            "message": "Не существует такой задачи"
        }
        return JsonResponse(json, safe=False, status=HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def my_results(request, contest_id, task_id):
    try:
        task = Task.objects.filter(contest=contest_id).get(id=task_id)
        efforts = Efforts.objects.filter(user_id=request.user.id, task_id=task_id)

        data = []
        for effort in efforts:
            json = {
                "id": task.id,
                "date_posted": effort.date_posted,
                "progress": {
                    "code": effort.solution_status,
                    "test_passed": effort.test_passed,
                    "test_count": task.efforts_available
                }
            }
            data.append(json)
        return JsonResponse(data, safe=False, status=HTTP_202_ACCEPTED)
    except ObjectDoesNotExist:
        json = {
            "message": "Не существует такой задачи"
        }
        return JsonResponse(json, safe=False, status=HTTP_404_NOT_FOUND)

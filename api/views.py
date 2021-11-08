import string

from api_yamdb.settings import SEND_MAIL
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from api.filters import TitleFilter
from api.mine_viewsets import ListCreateDestroyViewSet
from api.models import Category, Genre, Review, Title, User
from api.permissions import (IsAdminOrReadOnly, IsAdminRole,
                             IsStaffOrOwnerOrReadOnly)
from api.serializers import (CategorySerializer, CommentsSerializer,
                             GenresSerializer, MeSerializer, ReviewsSerializer,
                             TitlesCreateSerializer, TitlesReadSerializer,
                             UserSerializer)


@api_view(['POST'])
def send_code(request):
    if not request.data.get('email'):
        return Response(request.data, status=status.HTTP_400_BAD_REQUEST)
    newmail = request.data.get('email')
    user, created = User.objects.get_or_create(email=newmail,
                                               defaults={'username': newmail,
                                                         'is_active': 0})
    confirmation_code = default_token_generator.make_token(user)
    send_mail(
        'confirmation',
        confirmation_code,
        SEND_MAIL,
        [f'{newmail}'],
        fail_silently=False,
    )
    return Response(request.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def return_token(request):
    if not 'email' and 'confirmation_code' in request.data:
        return Response(request.data, status=status.HTTP_400_BAD_REQUEST)
    email = request.data.get('email')
    confirmation_code = request.data.get('confirmation_code')
    user = get_object_or_404(User, email=email)
    if default_token_generator.check_token(user=user, token=confirmation_code):
        if not user.is_active:
            user.is_active = True
            cleaner = str.maketrans(dict.fromkeys(string.punctuation))
            user.username = email.translate(cleaner)
            user.save()
        token = RefreshToken.for_user(user).access_token
        response = {"token": str(token)}
        st = status.HTTP_200_OK
    else:
        st = status.HTTP_204_NO_CONTENT
        response = {"message": "wrong conf code"}
    return Response(response, status=st)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'

    @action(detail=False, methods=['PATCH', 'GET'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = MeSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'PATCH':
            serializer = MeSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "you cant delite your account"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ReviewDetailViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsStaffOrOwnerOrReadOnly]

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class ReviewCommentDetailViewSet(viewsets.ModelViewSet):
    serializer_class = CommentsSerializer
    permission_classes = [IsStaffOrOwnerOrReadOnly]

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            pk=self.kwargs.get('review_id'),
            title=self.kwargs.get('title_id')
        )
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            pk=self.kwargs.get('review_id'),
            title=self.kwargs.get('title_id')
        )
        serializer.save(author=self.request.user, review=review)

    def perform_update(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CategoryViewSet(ListCreateDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenresViewSet(ListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenresSerializer


class GenreDelViewSet(mixins.DestroyModelMixin,  # DELETE-запросы
                      viewsets.GenericViewSet):
    serializer_class = GenresSerializer
    permission_classes = [IsAdminRole, ]

    def get_queryset(self):
        queryset = get_object_or_404(Genre, id=self.kwargs['id'])
        return queryset


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(rating=Avg('reviews__score'))
    pagination_class = PageNumberPagination
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return TitlesCreateSerializer
        return TitlesReadSerializer

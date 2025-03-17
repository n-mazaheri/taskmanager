from rest_framework import filters, viewsets
from django_filters.rest_framework import DjangoFilterBackend  # Correct import from django_filters.rest_framework
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import Task, Tag
from .serializers import TaskSerializer, TagSerializer
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as django_filters


class TaskPagination(PageNumberPagination):
    page_size = 10  # Set the number of tasks per page
    page_size_query_param = 'page_size'
    max_page_size = 100  # Max limit for page size


class TaskFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    priority = django_filters.CharFilter(field_name='priority', lookup_expr='iexact')
    assigned_to = django_filters.CharFilter(field_name='assigned_to__username', lookup_expr='iexact')
    tag = django_filters.CharFilter(field_name='tags__name', lookup_expr='iexact')
    due_date_start = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='gte')
    due_date_end = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='lte')

    class Meta:
        model = Task
        fields = ['status', 'priority', 'assigned_to', 'tag', 'due_date_start', 'due_date_end']


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    pagination_class = TaskPagination

    # Apply filters for TaskViewSet
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TaskFilter  # Use the custom TaskFilter class for filtering
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['created_at']

    def get_queryset(self):
        """
        Refactor to use DRF's filtering system to improve efficiency.
        This is done by leveraging DjangoFilterBackend and the filterset_class.
        """
        queryset = super().get_queryset()
        return queryset

    def perform_create(self, serializer):
        """
        Perform the creation of a Task instance, ensuring proper validation.
        """
        task = serializer.save()
        return task

    def handle_exception(self, exc):
        """
        Override to catch and return custom error messages for validation errors.
        """
        if isinstance(exc, ValidationError):
            return Response({'detail': str(exc)}, status=400)
        return super().handle_exception(exc)

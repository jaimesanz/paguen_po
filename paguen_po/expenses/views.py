from rest_framework import generics

from .models import Category
from .serializers import CategorySerializer


class CategoryList(generics.ListCreateAPIView):
    """Lists all Categories or creates a new one."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

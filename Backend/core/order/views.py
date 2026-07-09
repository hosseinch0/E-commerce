from rest_framework import generics, status
from rest_framework.response import Response
from .models import OrderModel
from .serializers import OrderSerializer
from .services import create_order_from_cart


class OrderListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return OrderModel.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        order = create_order_from_cart(request.user)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

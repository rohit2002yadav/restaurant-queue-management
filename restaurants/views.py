from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Restaurant, TableUnit


class RestaurantDetailView(APIView):
    def get(self, request, restaurant_id):
        try:
            r = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response({'error': 'Restaurant not found'}, status=status.HTTP_404_NOT_FOUND)

        available = TableUnit.objects.filter(restaurant=r, status='available').count()
        occupied = TableUnit.objects.filter(restaurant=r, status='occupied').count()

        return Response({
            'id': r.id,
            'name': r.name,
            'address': r.address,
            'avg_meal_duration_mins': r.avg_meal_duration_mins,
            'is_active': r.is_active,
            'available_tables': available,
            'occupied_tables': occupied,
        })

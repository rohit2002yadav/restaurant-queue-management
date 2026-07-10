from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from accounts.permissions import IsAdminRole
from .models import Restaurant, TableUnit


class RestaurantPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'address', 'is_active']


class TableUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TableUnit
        fields = ['id', 'table_number', 'capacity', 'status']


class RestaurantListView(APIView):
    def get(self, request):
        restaurants = Restaurant.objects.filter(is_active=True).order_by('name')
        return Response(RestaurantPublicSerializer(restaurants, many=True).data)


class RestaurantDetailView(APIView):
    def get(self, request, restaurant_id):
        try:
            r = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response({'error': 'Restaurant not found'}, status=status.HTTP_404_NOT_FOUND)

        counts = TableUnit.objects.filter(restaurant=r).aggregate(
            available=Count('id', filter=Q(status='available')),
            occupied=Count('id', filter=Q(status='occupied')),
        )

        return Response({
            'id': r.id,
            'name': r.name,
            'address': r.address,
            'avg_meal_duration_mins': r.avg_meal_duration_mins,
            'is_active': r.is_active,
            'available_tables': counts['available'],
            'occupied_tables': counts['occupied'],
        })


class TableListView(APIView):
    """GET /api/restaurants/<id>/tables/ — list all tables for admin's restaurant."""
    permission_classes = [IsAdminRole]

    def get(self, request, restaurant_id):
        if restaurant_id != getattr(request.user, 'restaurant_id', None):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        tables = TableUnit.objects.filter(restaurant_id=restaurant_id).order_by('table_number')
        return Response(TableUnitSerializer(tables, many=True).data)


class TableBulkCreateView(APIView):
    """POST /api/restaurants/<id>/tables/bulk-create/ — create tables from setup wizard."""
    permission_classes = [IsAdminRole]

    def post(self, request, restaurant_id):
        if restaurant_id != getattr(request.user, 'restaurant_id', None):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        tables_data = request.data.get('tables', [])
        if not tables_data or not isinstance(tables_data, list):
            return Response({'error': 'tables list is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response({'error': 'Restaurant not found'}, status=status.HTTP_404_NOT_FOUND)

        # Validate each entry
        for t in tables_data:
            cap = t.get('capacity', 0)
            if not isinstance(cap, int) or cap < 1 or cap > 20:
                return Response({'error': f"Invalid capacity {cap}. Must be 1–20."}, status=status.HTTP_400_BAD_REQUEST)

        created = TableUnit.objects.bulk_create([
            TableUnit(
                restaurant=restaurant,
                table_number=t['table_number'],
                capacity=t['capacity'],
                status='available',
            )
            for t in tables_data
        ])
        return Response({'created': len(created), 'message': f'{len(created)} tables created successfully.'}, status=status.HTTP_201_CREATED)


class TableDetailView(APIView):
    """PATCH/DELETE /api/restaurants/tables/<table_id>/"""
    permission_classes = [IsAdminRole]

    def _get_table(self, table_id, user):
        try:
            table = TableUnit.objects.select_related('restaurant').get(id=table_id)
        except TableUnit.DoesNotExist:
            return None, Response({'error': 'Table not found'}, status=status.HTTP_404_NOT_FOUND)
        if table.restaurant_id != getattr(user, 'restaurant_id', None):
            return None, Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        return table, None

    def patch(self, request, table_id):
        table, err = self._get_table(table_id, request.user)
        if err:
            return err
        capacity = request.data.get('capacity')
        if capacity is None or not isinstance(capacity, int) or capacity < 1 or capacity > 20:
            return Response({'error': 'capacity must be an integer between 1 and 20'}, status=status.HTTP_400_BAD_REQUEST)
        table.capacity = capacity
        table.save(update_fields=['capacity'])
        return Response(TableUnitSerializer(table).data)

    def delete(self, request, table_id):
        table, err = self._get_table(table_id, request.user)
        if err:
            return err
        if table.status == 'occupied':
            return Response({'error': 'Cannot delete an occupied table'}, status=status.HTTP_400_BAD_REQUEST)
        table.delete()
        return Response({'message': 'Table deleted successfully'}, status=status.HTTP_200_OK)

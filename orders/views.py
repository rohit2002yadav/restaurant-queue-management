from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.permissions import IsAdminRole

from .serializers import (
    MenuItemSerializer,
    CreateOrderSerializer,
    OrderRecordSerializer,
    UpdateOrderStatusSerializer,
    UpdateOrderItemStatusSerializer,
)
from .services import (
    get_menu_by_restaurant,
    create_order_service,
    update_order_status_service,
    update_order_item_status_service,
    get_orders_for_table_service,
    get_active_orders_service,
)
from .models import OrderRecord, OrderItem
from queue_manager.models import TableAssignment


def _admin_restaurant_id(request):
    """Return the restaurant_id the authenticated admin owns."""
    return getattr(request.user, 'restaurant_id', None)


def _assignment_restaurant_id(table_assignment_id):
    """Resolve the restaurant_id for a TableAssignment, or None if not found."""
    try:
        return TableAssignment.objects.select_related(
            'queue_entry__restaurant'
        ).get(id=table_assignment_id).queue_entry.restaurant_id
    except TableAssignment.DoesNotExist:
        return None


def _order_restaurant_id(order_id):
    """Resolve the restaurant_id for an OrderRecord, or None if not found."""
    try:
        return OrderRecord.objects.select_related(
            'table_assignment__queue_entry__restaurant'
        ).get(id=order_id).table_assignment.queue_entry.restaurant_id
    except OrderRecord.DoesNotExist:
        return None


def _item_restaurant_id(item_id):
    """Resolve the restaurant_id for an OrderItem, or None if not found."""
    try:
        return OrderItem.objects.select_related(
            'order__table_assignment__queue_entry__restaurant'
        ).get(id=item_id).order.table_assignment.queue_entry.restaurant_id
    except OrderItem.DoesNotExist:
        return None


# =========================================================
# GET MENU (Public - no auth required)
# =========================================================
class MenuView(APIView):
    def get(self, request, restaurant_id):
        try:
            menu_items = get_menu_by_restaurant(restaurant_id)

            if not menu_items.exists():
                return Response(
                    {"message": "No menu items available"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = MenuItemSerializer(menu_items, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================
# CREATE ORDER
# =========================================================
class CreateOrderView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        table_assignment_id = serializer.validated_data['table_assignment_id']

        # Ownership check: assignment must belong to this admin's restaurant
        resource_restaurant = _assignment_restaurant_id(table_assignment_id)
        if resource_restaurant is None:
            return Response(
                {"error": "Active table assignment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        if resource_restaurant != _admin_restaurant_id(request):
            return Response(
                {"error": "You do not have permission to order for this table"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            data = serializer.validated_data
            result = create_order_service(
                table_assignment_id=table_assignment_id,
                items_data=data['items'],
                notes=data.get('notes', '')
            )
            return Response(result, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================
# GET ORDER DETAILS
# =========================================================
class OrderDetailView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, order_id):
        resource_restaurant = _order_restaurant_id(order_id)
        if resource_restaurant is None:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        if resource_restaurant != _admin_restaurant_id(request):
            return Response(
                {"error": "You do not have permission to view this order"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            order = OrderRecord.objects.prefetch_related('items__menu_item').get(id=order_id)
            serializer = OrderRecordSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================================================
# UPDATE ORDER STATUS
# =========================================================
class UpdateOrderStatusView(APIView):
    permission_classes = [IsAdminRole]

    def patch(self, request, order_id):
        resource_restaurant = _order_restaurant_id(order_id)
        if resource_restaurant is None:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        if resource_restaurant != _admin_restaurant_id(request):
            return Response(
                {"error": "You do not have permission to update this order"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UpdateOrderStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = update_order_status_service(
                order_id=order_id,
                new_status=serializer.validated_data['status']
            )
            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================
# UPDATE ORDER ITEM STATUS
# =========================================================
class UpdateOrderItemStatusView(APIView):
    permission_classes = [IsAdminRole]

    def patch(self, request, item_id):
        resource_restaurant = _item_restaurant_id(item_id)
        if resource_restaurant is None:
            return Response({"error": "Order item not found"}, status=status.HTTP_404_NOT_FOUND)
        if resource_restaurant != _admin_restaurant_id(request):
            return Response(
                {"error": "You do not have permission to update this item"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UpdateOrderItemStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = update_order_item_status_service(
                order_item_id=item_id,
                new_status=serializer.validated_data['status']
            )
            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================
# GET ORDERS FOR TABLE
# =========================================================
class TableOrdersView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, table_assignment_id):
        resource_restaurant = _assignment_restaurant_id(table_assignment_id)
        if resource_restaurant is None:
            return Response(
                {"error": "Table assignment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        if resource_restaurant != _admin_restaurant_id(request):
            return Response(
                {"error": "You do not have permission to view this table's orders"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            orders = get_orders_for_table_service(table_assignment_id)
            serializer = OrderRecordSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================================================
# GET ACTIVE ORDERS FOR RESTAURANT
# =========================================================
class RestaurantActiveOrdersView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, restaurant_id):
        # URL param must match the authenticated admin's own restaurant
        if restaurant_id != _admin_restaurant_id(request):
            return Response(
                {"error": "You do not have permission to view this restaurant's orders"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            orders = get_active_orders_service(restaurant_id)
            serializer = OrderRecordSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

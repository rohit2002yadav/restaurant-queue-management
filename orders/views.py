from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser

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


# =========================================================
# GET MENU (Public - no auth required)
# =========================================================
class MenuView(APIView):
    """
    GET /api/orders/menu/<restaurant_id>/

    Returns: List of available menu items for restaurant
    """

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
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = serializer.validated_data
            result = create_order_service(
                table_assignment_id=data['table_assignment_id'],
                items_data=data['items'],
                notes=data.get('notes', '')
            )

            return Response(result, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================
# GET ORDER DETAILS
# =========================================================
class OrderDetailView(APIView):
    """
    GET /api/orders/<order_id>/

    Returns: Full order details with all items
    """

    permission_classes = [IsAdminUser]

    def get(self, request, order_id):
        try:
            from .models import OrderRecord

            order = OrderRecord.objects.prefetch_related(
                'items__menu_item'
            ).get(id=order_id)

            serializer = OrderRecordSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except OrderRecord.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================
# UPDATE ORDER STATUS
# =========================================================
class UpdateOrderStatusView(APIView):
    """
    PATCH /api/orders/<order_id>/status/

    Payload:
    {"status": "confirmed"}

    Valid statuses: pending, confirmed, preparing, ready, delivered, completed
    """

    permission_classes = [IsAdminUser]

    def patch(self, request, order_id):
        serializer = UpdateOrderStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = update_order_status_service(
                order_id=order_id,
                new_status=serializer.validated_data['status']
            )

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================
# UPDATE ORDER ITEM STATUS
# =========================================================
class UpdateOrderItemStatusView(APIView):
    """
    PATCH /api/orders/item/<item_id>/status/

    Payload:
    {"status": "ready"}

    Valid statuses: pending, preparing, ready, served
    """

    permission_classes = [IsAdminUser]

    def patch(self, request, item_id):
        serializer = UpdateOrderItemStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = update_order_item_status_service(
                order_item_id=item_id,
                new_status=serializer.validated_data['status']
            )

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================
# GET ORDERS FOR TABLE
# =========================================================
class TableOrdersView(APIView):
    """
    GET /api/orders/table/<table_assignment_id>/

    Returns: All orders for a specific table
    """

    permission_classes = [IsAdminUser]

    def get(self, request, table_assignment_id):
        try:
            orders = get_orders_for_table_service(table_assignment_id)

            serializer = OrderRecordSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================
# GET ACTIVE ORDERS FOR RESTAURANT (Kitchen Dashboard)
# =========================================================
class RestaurantActiveOrdersView(APIView):
    """
    GET /api/orders/restaurant/<restaurant_id>/active/

    Kitchen staff view: All active orders for the restaurant

    Returns: Orders with status in (pending, confirmed, preparing, ready)
    """

    permission_classes = [IsAdminUser]

    def get(self, request, restaurant_id):
        try:
            orders = get_active_orders_service(restaurant_id)

            serializer = OrderRecordSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.permissions import IsAdminRole
from .serializers import (
    JoinQueueSerializer,
    QueueEntrySerializer,
    TableAssignmentSerializer,
)
from .services import (
    call_customer_service,
    clear_table_service,
    join_queue_service,
    leave_queue_service,
)
from .models import QueueEntry, TableAssignment


def _admin_restaurant_id(request):
    """Return the restaurant_id the authenticated admin owns."""
    return getattr(request.user, 'restaurant_id', None)


class JoinQueueView(APIView):

    def post(self, request):
        serializer = JoinQueueSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = join_queue_service(serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class QueueStatusView(APIView):

    def get(self, request, token):
        entry = QueueEntry.objects.select_related('customer', 'restaurant').filter(
            token_number=token
        ).order_by('-id').first()

        if entry is None:
            return Response({"error": "Token not found"}, status=status.HTTP_404_NOT_FOUND)

        people_ahead = 0
        position = 0

        if entry.status == 'waiting':
            people_ahead = QueueEntry.objects.filter(
                restaurant=entry.restaurant,
                status='waiting',
                queue_type=entry.queue_type,
                joined_at__lt=entry.joined_at,
                expires_at__isnull=True
            ).count()
            position = people_ahead + 1

        serializer = QueueEntrySerializer(entry)
        return Response({
            "queue_entry": serializer.data,
            "position": position,
            "people_ahead": people_ahead,
            "status": entry.status
        })


class RestaurantQueueView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, restaurant_id):
        # Enforce: staff can only view their own restaurant
        if restaurant_id != _admin_restaurant_id(request):
            return Response(
                {"error": "You do not have permission to view this restaurant's queue"},
                status=status.HTTP_403_FORBIDDEN
            )

        entries = QueueEntry.objects.filter(
            restaurant_id=restaurant_id,
            status='waiting'
        ).select_related('customer')

        return Response(QueueEntrySerializer(entries, many=True).data)


class StaffDashboardView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, restaurant_id):
        # Enforce: staff can only view their own restaurant
        if restaurant_id != _admin_restaurant_id(request):
            return Response(
                {"error": "You do not have permission to view this restaurant's dashboard"},
                status=status.HTTP_403_FORBIDDEN
            )

        waiting_entries = QueueEntry.objects.filter(
            restaurant_id=restaurant_id,
            status='waiting'
        ).select_related('customer').order_by('joined_at')

        active_assignments = TableAssignment.objects.filter(
            table_unit__restaurant_id=restaurant_id,
            is_active=True
        ).select_related(
            'queue_entry__customer',
            'table_unit',
        ).order_by('assigned_at')

        return Response({
            'waiting_queue': QueueEntrySerializer(waiting_entries, many=True).data,
            'active_tables': TableAssignmentSerializer(active_assignments, many=True).data,
        })


class ClearTableView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        table_assignment_id = request.data.get('table_assignment_id')
        if not table_assignment_id:
            return Response(
                {"error": "table_assignment_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ownership check: the assignment must belong to this admin's restaurant
        try:
            assignment = TableAssignment.objects.select_related(
                'table_unit__restaurant'
            ).get(id=table_assignment_id, is_active=True)
        except TableAssignment.DoesNotExist:
            return Response(
                {"error": "Active table assignment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if assignment.table_unit.restaurant_id != _admin_restaurant_id(request):
            return Response(
                {"error": "You do not have permission to clear this table"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            result = clear_table_service(table_assignment_id)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LeaveQueueView(APIView):

    def post(self, request):
        token = request.data.get('token')
        restaurant_id = request.data.get('restaurant_id')

        if not token or not restaurant_id:
            return Response(
                {"error": "token and restaurant_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = leave_queue_service(token, restaurant_id)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CallCustomerView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        queue_entry_id = request.data.get('queue_entry_id')
        if not queue_entry_id:
            return Response(
                {"error": "queue_entry_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ownership check: queue entry must belong to this admin's restaurant
        try:
            entry = QueueEntry.objects.select_related('restaurant').get(
                id=queue_entry_id, status='waiting'
            )
        except QueueEntry.DoesNotExist:
            return Response(
                {"error": "Queue entry not found or not waiting"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if entry.restaurant_id != _admin_restaurant_id(request):
            return Response(
                {"error": "You do not have permission to call this customer"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            result = call_customer_service(queue_entry_id)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

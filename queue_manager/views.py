from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import JoinQueueSerializer, QueueEntrySerializer
from .services import join_queue_service, clear_table_service, leave_queue_service
from .models import QueueEntry
from .tasks import call_next_customer



# =========================================================
# JOIN QUEUE VIEW
# Purpose:
# Entry point when customer submits join form
# =========================================================
class JoinQueueView(APIView):

    def post(self, request):
        # 1️⃣ Validate incoming payload
        serializer = JoinQueueSerializer(data=request.data)
        if not serializer.is_valid():
            # WHY:
            # → Never trust client input
            # → Return clear validation errors to frontend
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2️⃣ Get restaurant_id
        # Prefer body over query params for POST (more consistent)
        restaurant_id = request.data.get('restaurant_id')
        if not restaurant_id:
            return Response(
                {"error": "restaurant_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3️⃣ Call business logic (service layer)
        try:
            data = serializer.validated_data
            data['restaurant_id'] = restaurant_id

            result = join_queue_service(data)

            # WHY 201:
            # → New resource (queue entry) is created
            return Response(result, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # WHY:
            # → Service raises domain errors
            # → View converts to HTTP response
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# =========================================================
# QUEUE STATUS VIEW
# Purpose:
# Customer checks their live queue status using token
# =========================================================
class QueueStatusView(APIView):

    def get(self, request, token):
        # 1️⃣ Fetch queue entry
        try:
            entry = QueueEntry.objects.select_related('customer', 'restaurant').get(
                token_number=token
            )
        except QueueEntry.DoesNotExist:
            return Response(
                {"error": "Token not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2️⃣ Calculate people ahead only if customer is still waiting
        # WHY:
        # → Seated/completed customers don't need position info
        # → Only count WAITING entries in SAME queue_type joined BEFORE this customer
        people_ahead = 0
        position = 0

        if entry.status == 'waiting':
            people_ahead = QueueEntry.objects.filter(
                restaurant=entry.restaurant,
                status='waiting',
                queue_type=entry.queue_type,
                joined_at__lt=entry.joined_at
            ).count()
            # position = people ahead + 1
            # 0 people ahead → position 1 (next to be seated)
            position = people_ahead + 1

        # 3️⃣ Serialize current entry
        serializer = QueueEntrySerializer(entry)

        # 4️⃣ Return combined response
        return Response({
            "queue_entry": serializer.data,
            "position": position,
            "people_ahead": people_ahead,
            "status": entry.status
        })


# =========================================================
# RESTAURANT QUEUE VIEW (STAFF DASHBOARD)
# Purpose:
# Staff sees current waiting queue
# =========================================================
class RestaurantQueueView(APIView):

    def get(self, request, restaurant_id):
        # 1️⃣ Fetch only waiting customers
        entries = QueueEntry.objects.filter(
            restaurant_id=restaurant_id,
            status='waiting'
        ).select_related('customer')
        # WHY select_related:
        # → Avoid N+1 query problem
        # → Fetch customer in same DB query

        # 2️⃣ Serialize list
        serializer = QueueEntrySerializer(entries, many=True)

        # 3️⃣ Return list
        return Response(serializer.data)
    

class ClearTableView(APIView):
    # Handles POST /api/queue/clear-table/
    # Called by staff when customer finishes eating

    def post(self, request):
        table_assignment_id = request.data.get('table_assignment_id')

        # 1️⃣ Validate input
        if not table_assignment_id:
            return Response(
                {"error": "table_assignment_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 2️⃣ Call service layer (business logic)
            result = clear_table_service(table_assignment_id)

            # 3️⃣ Return success response
            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            # Known business error (e.g., invalid assignment)
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:
            # 🔥 Safety fallback (important in production)
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class LeaveQueueView(APIView):
    # Handles POST /api/queue/leave-queue/

    def post(self, request):
        token = request.data.get('token')
        restaurant_id = request.data.get('restaurant_id')

        # 1️⃣ Validate input
        if not token or not restaurant_id:
            return Response(
                {"error": "token and restaurant_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 2️⃣ Call service
            result = leave_queue_service(token, restaurant_id)

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


class CallCustomerView(APIView):
    # Handles POST /api/queue/call-customer/
    # Staff taps "Call" button

    def post(self, request):
        queue_entry_id = request.data.get('queue_entry_id')

        # 1️⃣ Validate input
        if not queue_entry_id:
            return Response(
                {"error": "queue_entry_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 2️⃣ Trigger Celery task asynchronously
            call_next_customer.delay(queue_entry_id)

            # WHY:
            # → Non-blocking
            # → Scalable
            # → Future-ready (SMS, notifications)

            return Response(
                {"message": "Customer is being called"},
                status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
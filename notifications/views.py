from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.permissions import IsAdminRole

from .serializers import SubmitFeedbackSerializer, FeedbackSerializer, NotificationLogSerializer
from .models import Feedback, NotificationLog
from queue_manager.models import QueueEntry


class SubmitFeedbackView(APIView):
    def post(self, request):
        serializer = SubmitFeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data  = serializer.validated_data
        token = data['token_number']

        try:
            queue_entry = QueueEntry.objects.select_related('customer').get(
                token_number=token,
                status='completed'
            )
        except QueueEntry.DoesNotExist:
            return Response({'error': 'No completed visit found for this token'}, status=status.HTTP_404_NOT_FOUND)

        if Feedback.objects.filter(queue_entry=queue_entry).exists():
            return Response({'error': 'Feedback already submitted for this visit'}, status=status.HTTP_400_BAD_REQUEST)

        feedback = Feedback.objects.create(
            queue_entry=queue_entry,
            overall_rating=data['overall_rating'],
            wait_satisfaction=data['wait_satisfaction'],
            food_rating=data['food_rating'],
            service_rating=data['service_rating'],
            would_recommend=data.get('would_recommend'),
            comment=data.get('comment', ''),
        )

        return Response(FeedbackSerializer(feedback).data, status=status.HTTP_201_CREATED)


class RestaurantFeedbackView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, restaurant_id):
        feedbacks = Feedback.objects.filter(
            queue_entry__restaurant_id=restaurant_id
        ).select_related('queue_entry__customer').order_by('-submitted_at')

        return Response(FeedbackSerializer(feedbacks, many=True).data)


class NotificationLogsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, restaurant_id):
        logs = NotificationLog.objects.filter(
            queue_entry__restaurant_id=restaurant_id
        ).select_related('queue_entry').order_by('-sent_at')[:100]

        return Response(NotificationLogSerializer(logs, many=True).data)

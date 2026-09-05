import uuid
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from core.permissions import IsAdmin, IsEmployer
from .models import PaymentTransaction
from rest_framework.permissions import IsAuthenticated
from .models import UserSubscription
from .subscription_permissions import HasActiveSubscription, IsEmployerUser
from django.db.models import Count, Avg
from django.db.models import Sum

class CreatePaymentOrderAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        amount = request.data.get("amount")

        if not amount:
            return Response(
                {"error": "Amount is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction_id = f"MOCK_{uuid.uuid4().hex[:12]}"

        transaction = PaymentTransaction.objects.create(
            user=request.user,
            amount=amount,
            transaction_id=transaction_id,
            status="pending"
        )

        return Response({
            "status": "success",
            "message": "Payment order created",
            "order_id": transaction_id,
            "amount": amount,
            "currency": "INR",
            "payment_status": "pending"
        })

class VerifyPaymentAPI(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        order_id = request.data.get("order_id")
        payment_id = request.data.get("payment_id")

        if not order_id or not payment_id:
            return Response(
                {
                    "error": "order_id and payment_id are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            transaction = PaymentTransaction.objects.get(
                transaction_id=order_id,
                user=request.user
            )

            transaction.status = "success"
            transaction.save()

            return Response({
                "status": "success",
                "message": "Payment verified successfully",
                "order_id": order_id,
                "payment_id": payment_id,
                "payment_status": "success"
            })

        except PaymentTransaction.DoesNotExist:
            return Response(
                {
                    "error": "Payment transaction not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )




class PaymentWebhookAPI(APIView):

    def post(self, request):

        try:
            data = request.data

            event = data.get("event")

            if event == "payment.success":

                payment_id = data.get("payment_id")

                return Response({
                    "status": "success",
                    "message": "Payment success webhook received",
                    "payment_id": payment_id
                })

            elif event == "payment.failed":

                payment_id = data.get("payment_id")

                return Response({
                    "status": "failed",
                    "message": "Payment failure webhook received",
                    "payment_id": payment_id
                })

            elif event == "refund.created":

                payment_id = data.get("payment_id")

                return Response({
                    "status": "refund",
                    "message": "Refund webhook received",
                    "payment_id": payment_id
                })

            return Response({
                "status": "ignored",
                "message": "Unknown webhook event"
            })

        except Exception as e:

            return Response(
                {
                    "status": "error",
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class SubscriptionStatusAPI(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        subscription = UserSubscription.objects.filter(
            user=request.user,
            end_date__gt=timezone.now()
        ).order_by("-end_date").first()

        if subscription:
            return Response({
                "active": True,
                "plan": subscription.plan.name,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date
            })

        return Response({
            "active": False,
            "plan": None,
            "message": "No active subscription found"
        })

class PremiumFeatureAPI(APIView):

    permission_classes = [
        IsAuthenticated,
        HasActiveSubscription
    ]

    def get(self, request):

        return Response({
            "status": "success",
            "message": "Premium feature access granted",
            "plan": "Paid subscription"
        })


class PremiumRecruiterAnalyticsAPI(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployer,
        HasActiveSubscription
    ]

    def get(self, request):

        subscription = UserSubscription.objects.filter(
            user=request.user,
            end_date__gt=timezone.now()
        ).order_by("-end_date").first()

        if not subscription:
            return Response(
                {
                    "status": "error",
                    "message": "Active subscription required"
                },
                status=403
            )

        plan = subscription.plan

        if not plan.ai_analytics:
            return Response(
                {
                    "status": "error",
                    "message": "AI analytics requires a premium plan"
                },
                status=403
            )

        return Response({
            "status": "success",
            "plan": plan.name,
            "report": {
                "total_candidates": 0,
                "shortlisted_candidates": 0,
                "successful_candidates": 0,
                "hiring_efficiency": "High"
            },
            "message": "Premium recruiter analytics available"
        })

class AdminBillingAPI(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get(self, request):

        transactions = PaymentTransaction.objects.all().order_by("-id")

        data = []

        for transaction in transactions:
            data.append({
                "transaction_id": transaction.transaction_id,
                "amount": str(transaction.amount),
                "status": transaction.status,
            })

        return Response({
            "status": "success",
            "total_transactions": transactions.count(),
            "transactions": data
        })

class AdminTransactionListAPI(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get(self, request):

        transactions = PaymentTransaction.objects.all().order_by("-id")

        data = []

        for transaction in transactions:
            data.append({
                "id": transaction.id,
                "transaction_id": transaction.transaction_id,
                "amount": str(transaction.amount),
                "status": transaction.status,
            })

        return Response({
            "status": "success",
            "count": transactions.count(),
            "transactions": data
        })

class AdminRevenueReportAPI(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get(self, request):

        successful_transactions = PaymentTransaction.objects.filter(
            status="success"
        )

        total_revenue = successful_transactions.aggregate(
            total=Sum("amount")
        )["total"] or 0

        return Response({
            "status": "success",
            "total_revenue": str(total_revenue),
            "successful_transactions": successful_transactions.count()
        })
from django.db import models


class ComplaintStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_REVIEW = "in_review", "In Review"
    PENDING_USER = "pending_user", "Pending User Response"
    RESOLVED = "resolved", "Resolved"
    CLOSED = "closed", "Closed"
    REJECTED = "rejected", "Rejected"


class ComplaintType(models.TextChoices):
    ORDER_ISSUE = "order_issue", "Order Issue"
    WRONG_ITEM = "wrong_item", "Wrong Item"
    MISSING_ITEM = "missing_item", "Missing Item"
    LATE_DELIVERY = "late_delivery", "Late Delivery"
    COURIER_BEHAVIOR = "courier_behavior", "Courier Behavior"
    MERCHANT_BEHAVIOR = "merchant_behavior", "Merchant Behavior"
    PAYMENT_ISSUE = "payment_issue", "Payment Issue"
    APP_BUG = "app_bug", "App Bug"
    OTHER = "other", "Other"


class DisputeStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    UNDER_INVESTIGATION = "under_investigation", "Under Investigation"
    RESOLVED_REFUND = "resolved_refund", "Resolved with Refund"
    RESOLVED_NO_REFUND = "resolved_no_refund", "Resolved without Refund"
    ESCALATED = "escalated", "Escalated"
    CLOSED = "closed", "Closed"


class RefundRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    PROCESSED = "processed", "Processed"
    CANCELLED = "cancelled", "Cancelled"


class RefundReason(models.TextChoices):
    MISSING_ITEM = "missing_item", "Missing Item"
    WRONG_ITEM = "wrong_item", "Wrong Item"
    QUALITY_ISSUE = "quality_issue", "Quality Issue"
    LATE_DELIVERY = "late_delivery", "Late Delivery"
    ORDER_CANCELLED = "order_cancelled", "Order Cancelled"
    DUPLICATE_PAYMENT = "duplicate_payment", "Duplicate Payment"
    OTHER = "other", "Other"


class MessageSender(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    SUPPORT = "support", "Support Agent"
    SYSTEM = "system", "System"


class TicketPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"

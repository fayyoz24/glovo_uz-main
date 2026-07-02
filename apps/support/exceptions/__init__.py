from rest_framework.exceptions import APIException
from rest_framework import status


class ComplaintNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Complaint not found."
    default_code = "complaint_not_found"


class ComplaintAlreadyClosed(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This complaint is already closed."
    default_code = "complaint_already_closed"


class DisputeNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Dispute not found."
    default_code = "dispute_not_found"


class RefundRequestNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Refund request not found."
    default_code = "refund_request_not_found"


class RefundAlreadyProcessed(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Refund request has already been processed."
    default_code = "refund_already_processed"


class InvalidStatusTransition(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid status transition."
    default_code = "invalid_status_transition"


class DuplicateComplaint(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "An open complaint already exists for this order."
    default_code = "duplicate_complaint"

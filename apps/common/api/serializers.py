from rest_framework import serializers


class WritableSerializerMixin:
    """
    Mixin that separates read (output) from write (input) fields.
    Override write_fields or read_fields in subclass as needed.
    """
    pass


class TimestampMixin(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

from rest_framework import serializers


class AnalyticsQuerySerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=["today", "week", "month", "custom"], required=False, default="week")
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if attrs.get("period") == "custom":
            if not attrs.get("start_date") or not attrs.get("end_date"):
                raise serializers.ValidationError("start_date and end_date are required when period=custom")
            if attrs["start_date"] > attrs["end_date"]:
                raise serializers.ValidationError("start_date cannot be greater than end_date")
        return attrs

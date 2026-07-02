class AnalyticsError(Exception):
    default_message = "Analytics error"

    def __init__(self, message=None):
        super().__init__(message or self.default_message)


class InvalidAnalyticsPeriodError(AnalyticsError):
    default_message = "Invalid analytics period."


class AnalyticsAggregationError(AnalyticsError):
    default_message = "Analytics aggregation failed."

from celery import shared_task
from apps.analytics.services.aggregation_service import AnalyticsAggregationService


@shared_task(bind=True, max_retries=3)
def build_daily_analytics_snapshot_task(self, date=None):
    AnalyticsAggregationService.build_daily_snapshot(date=date)

import json
from datetime import timedelta
from django.utils import timezone
from core.models import RequestLog, AnalysisResult  # Import your models
from django.db.models import Count, Sum, Case, When, Value, IntegerField, Avg, F, Q
from django.db.models.functions import TruncHour, TruncDay
from collections import defaultdict
from django.http import JsonResponse  # For sending JSON response (if used as a view)
class VividmindTaskAnalysis:

    def analyze_failed_requests(self, time_delta=timedelta(days=7)):
        range_end = timezone.now()
        range_start = self.get_last_analysis_range('analyze_failed_requests') or range_end - time_delta
        request_logs = RequestLog.objects.filter(datetime__range=(range_start, range_end), status_code__range=(400, 599))

        failed_request_counts = request_logs.values('end_point', 'r_type').annotate(count=Count('id'))
        data = list(failed_request_counts)

        self.save_analysis_result('analyze_failed_requests', data, range_start, range_end)
        return data
class CentralRequestingAnalysis:
    def analyze_central_logs(self):
        pass
class StorageHouseRequestingAnalysis:
    def analyze_storagehouse_requestlogs(self):
        pass
class InstagramAutomationAnalysis:
    def analyze_automation_logs(self):
        pass
class InstagramScrapingAnalysis:
    def analyze_scraping_logs(self):
        pass
class DeviceAnalysis:
    def analyze_device_logs(self):
        pass
class ServerAnalysis:
    def analyze_server_logs(self):
        pass
class OpenAiAnalysis:
    def analyze_openai_analysis_logs(self):
        pass
class AudienceAnalysis:
    def analyze_audience_logs(self):
        pass
class ScrapeTaskAnalysis:
    def analyze_scrapetask_logs(self):
        pass
class DownloadAnalysis:
    def analyze_downloads_logs(self):
        pass
    def analyze_successful_downloads_with_respect_to_service(self):
        pass
        from core.models import Log
        download_logs=Log.objects.all().filter(type='downloaded_file')
    def analyze_successful_downloads_with_respect_to_endpoint(self):
        pass
def analyze_request_logs_nested_with_counts():
    """
    Analyzes request logs and creates a nested dictionary structure with success/failure counts.

    Returns:
        A nested dictionary containing the analysis results with counts.
    """

    nested_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"statuses": set(), "success_count": 0, "fail_count": 0}))))

    results = RequestLog.objects.values(
        'service', 'end_point', 'data_point', 'r_type', 'status_code'
    ).distinct()
    print(results)
    for item in results:
        service = item['service']
        end_point = item['end_point']
        data_point = item['data_point']
        r_type = item['r_type']
        status = item['status_code']

        nested_data[service][end_point][data_point][r_type]["statuses"].add(status)
        if 200 <= status < 300:  # Success (2xx)
            nested_data[service][end_point][data_point][r_type]["success_count"] += 1
        else:  # Failure (non-2xx)
            nested_data[service][end_point][data_point][r_type]["fail_count"] += 1

    # Aggregate counts at higher levels
    print(nested_data.items())
    for service, end_points in nested_data.items():
        service_success = 0
        service_fail = 0
        for end_point, data_points in end_points.items():
            endpoint_success = 0
            endpoint_fail = 0
            for data_point, r_types in data_points.items():
                data_point_success = 0
                data_point_fail = 0
                for r_type_data in r_types.values():
                    data_point_success += r_type_data["success_count"]
                    data_point_fail += r_type_data["fail_count"]
                end_points[end_point]["success_count"] = endpoint_success + data_point_success
                end_points[end_point]["fail_count"] = endpoint_fail + data_point_fail

            service_success += endpoint_success
            service_fail += endpoint_fail
        nested_data[service]["success_count"] = service_success
        nested_data[service]["fail_count"] = service_fail
    print(nested_data.items())
    # Convert sets to lists for JSON serialization
    for service, end_points in nested_data.items():
        for end_point, data_points in end_points.items():
            for data_point, r_types in data_points.items():
                for r_type, data in r_types.items():
                    nested_data[service][end_point][data_point][r_type]["statuses"] = list(data["statuses"])
    print(nested_data.items())
    return nested_data


def create_chart_data(analysis_results):
    """
    Transforms the nested analysis results into a format suitable for Chart.js (example).

    Args:
        analysis_results: The nested dictionary from the analysis function.

    Returns:
        A dictionary containing the chart data.
    """

    labels = []  # Service names
    success_data = []
    failure_data = []

    for service, data in analysis_results.items():
        if isinstance(data, dict) and "success_count" in data and "fail_count" in data: # check if it is service level
            labels.append(service)
            success_data.append(data["success_count"])
            failure_data.append(data["fail_count"])

    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": "Successful Requests",
                "data": success_data,
                "backgroundColor": "green",  # Customize colors
            },
            {
                "label": "Failed Requests",
                "data": failure_data,
                "backgroundColor": "red",
            },
        ],
    }
    return chart_data


def get_chart_data_json(request=None):  # Can be used as standalone or in a view
    """
    Combines analysis and chart data creation.  Returns JSON.
    """
    analysis_data = analyze_request_logs_nested_with_counts()
    chart_data = create_chart_data(analysis_data)
    return json.dumps(chart_data)  # Return JSON string


# Example usage (standalone script):

# Example usage as a Django view (if needed):
# def my_chart_view(request):
#     chart_json = get_chart_data_json(request)
#     return JsonResponse(json.loads(chart_json), safe=False) # safe=False because it is not a dict.
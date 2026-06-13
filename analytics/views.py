import json

from django.http import JsonResponse
from django.shortcuts import render

from analytics import services


def status(request):
    return JsonResponse({"ready": services.is_ready()})


def index(request):
    if not services.ensure_artifacts():
        return render(request, "analytics/index.html", {"computing": True})

    labels, bookings_data, adr_data, avg_adr, avg_room_occupy = (
        services.get_monthly_aggregations()
    )
    row_idx = int(request.GET.get("row", 79))
    waterfall_payload = services.get_waterfall_explanation(row_idx)

    context = {
        "computing": False,
        "avg_adr": avg_adr,
        "avg_room_occupy": avg_room_occupy,
        "chart_label_json": json.dumps(labels),
        "chart_data_json": json.dumps(bookings_data),
        "chart_adr_json": json.dumps(adr_data),
        "shap_box_json": json.dumps(services.get_box_plot()),
        "shap_waterfall_json": json.dumps(waterfall_payload),
    }
    return render(request, "analytics/index.html", context)

from django.shortcuts import render

from analytics import services


def index(request):
    shap_ready = services.ensure_artifacts()
    top_features = services.get_top_features(top_n=5) if shap_ready else []

    bar_colors = ["bg-primary", "bg-info", "bg-warning", "bg-secondary", "bg-success"]
    for i, f in enumerate(top_features):
        f["color"] = bar_colors[i % len(bar_colors)]

    context = {
        "shap_ready": shap_ready,
        "top_features": top_features,
    }
    return render(request, "ai_insights/index.html", context)

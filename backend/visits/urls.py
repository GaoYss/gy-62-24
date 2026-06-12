from django.urls import path

from . import views


urlpatterns = [
    path("dashboard-stats/", views.dashboard_stats),
    path("", views.visits_collection),
    path("<int:pk>/", views.visit_detail),
]

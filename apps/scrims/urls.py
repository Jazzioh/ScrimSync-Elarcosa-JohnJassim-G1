from django.urls import path
from . import views

app_name = "scrims"

urlpatterns = [
    path("teams/", views.TeamListView.as_view(), name="team_list"),
    path("teams/create/", views.TeamCreateView.as_view(), name="team_create"),
    path("teams/<int:pk>/edit/", views.TeamUpdateView.as_view(), name="team_edit"),
    path("teams/<int:pk>/delete/", views.TeamDeleteView.as_view(), name="team_delete"),
    path("teams/<int:pk>/join/", views.TeamJoinRequestCreateView.as_view(), name="team_join_request"),
    path("join-requests/<int:pk>/respond/", views.TeamJoinRequestRespondView.as_view(), name="team_join_respond"),
    path("", views.ScrimmageListView.as_view(), name="scrim_list"),
    path("create/", views.ScrimmageCreateView.as_view(), name="scrim_create"),
    path("<int:pk>/edit/", views.ScrimmageUpdateView.as_view(), name="scrim_edit"),
    path("<int:pk>/accept/", views.ScrimmageAcceptView.as_view(), name="scrim_accept"),
    path("<int:pk>/delete/", views.ScrimmageDeleteView.as_view(), name="scrim_delete"),
]

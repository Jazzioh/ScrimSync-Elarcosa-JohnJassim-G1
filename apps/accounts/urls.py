from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("dashboard/", views.RoleRedirectView.as_view(), name="role_redirect"),
    path("dashboard/admin/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("dashboard/admin/users/<int:pk>/edit/", views.AdminUserUpdateView.as_view(), name="admin_user_edit"),
    path("dashboard/admin/users/<int:pk>/delete/", views.AdminUserDeleteView.as_view(), name="admin_user_delete"),
    path("dashboard/manager/", views.ManagerDashboardView.as_view(), name="manager_dashboard"),
    path("dashboard/player/", views.PlayerDashboardView.as_view(), name="player_dashboard"),
    path("dashboard/organizer/", views.OrganizerDashboardView.as_view(), name="organizer_dashboard"),
    path("profile/", views.ProfileDetailView.as_view(), name="profile_detail"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_update"),
]
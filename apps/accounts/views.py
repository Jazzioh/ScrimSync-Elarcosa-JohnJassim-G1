from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView

from .forms import UserProfileUpdateForm, UserRegistrationForm
from .mixins import RoleRequiredMixin
from .models import User


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:role_redirect")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:role_redirect")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f"Welcome to ScrimSync, {user.username}! Your account has been created.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Registration failed. Please fix the errors below.")
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You have been logged out securely.")
        return super().dispatch(request, *args, **kwargs)


class RoleRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        role_routes = {
            User.Role.TEAM_MANAGER: "accounts:manager_dashboard",
            User.Role.PLAYER: "accounts:player_dashboard",
            User.Role.ORGANIZER: "accounts:organizer_dashboard",
        }
        return redirect(role_routes.get(request.user.role, "accounts:player_dashboard"))


class ManagerDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (User.Role.TEAM_MANAGER,)
    template_name = "accounts/dashboards/manager_dashboard.html"


class PlayerDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (User.Role.PLAYER,)
    template_name = "accounts/dashboards/player_dashboard.html"


class OrganizerDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (User.Role.ORGANIZER,)
    template_name = "accounts/dashboards/organizer_dashboard.html"


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "accounts/profile_detail.html"
    context_object_name = "profile_user"

    def get_object(self, queryset=None):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileUpdateForm
    template_name = "accounts/profile_update.html"
    success_url = reverse_lazy("accounts:profile_detail")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been updated.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Could not update profile. Please fix the highlighted errors.")
        return super().form_invalid(form)
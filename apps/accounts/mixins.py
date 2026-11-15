from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.role not in self.allowed_roles:
            messages.error(request, "Access denied: You do not have permission to access that dashboard.")
            return redirect("accounts:role_redirect")

        return super().dispatch(request, *args, **kwargs)
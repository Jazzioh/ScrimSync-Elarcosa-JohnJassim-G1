from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Team, TeamJoinRequest, Scrimmage
from .forms import TeamForm, TeamJoinRequestForm, ScrimmageForm, ScrimmageAcceptForm


class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = "scrims/team_list.html"
    context_object_name = "teams"

    def get_queryset(self):
        return Team.objects.select_related("manager").prefetch_related("members", "join_requests__player").order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["join_form"] = TeamJoinRequestForm()
        return context


class TeamCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = "scrims/team_form.html"
    success_url = reverse_lazy("scrims:team_list")

    def test_func(self):
        return self.request.user.role in ["MANAGER", "ADMIN"] or self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.manager = self.request.user
        messages.success(self.request, "Team created successfully!")
        return super().form_valid(form)


class TeamUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = "scrims/team_form.html"
    success_url = reverse_lazy("scrims:team_list")

    def test_func(self):
        team = self.get_object()
        return team.manager == self.request.user or self.request.user.role == "ADMIN" or self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, "Team roster details updated.")
        return super().form_valid(form)


class TeamDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Team
    template_name = "scrims/team_confirm_delete.html"
    success_url = reverse_lazy("scrims:team_list")

    def test_func(self):
        team = self.get_object()
        return team.manager == self.request.user or self.request.user.role == "ADMIN" or self.request.user.is_superuser


class TeamJoinRequestCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        if request.user in team.members.all() or team.manager == request.user:
            messages.warning(request, "You are already part of this team.")
            return redirect("scrims:team_list")

        existing = TeamJoinRequest.objects.filter(team=team, player=request.user, status="PENDING").exists()
        if existing:
            messages.info(request, "You already have a pending join request for this team.")
            return redirect("scrims:team_list")

        form = TeamJoinRequestForm(request.POST)
        if form.is_valid():
            join_req = form.save(commit=False)
            join_req.team = team
            join_req.player = request.user
            join_req.save()
            messages.success(request, f"Join request sent to {team.name}!")
        return redirect("scrims:team_list")


class TeamJoinRequestRespondView(LoginRequiredMixin, View):
    def post(self, request, pk):
        join_req = get_object_or_404(TeamJoinRequest, pk=pk)
        if join_req.team.manager != request.user and not request.user.is_superuser:
            messages.error(request, "Only the Team Manager can approve or decline requests.")
            return redirect("scrims:team_list")

        action = request.POST.get("action")
        if action == "accept":
            join_req.status = "ACCEPTED"
            join_req.save()
            join_req.team.members.add(join_req.player)
            messages.success(request, f"{join_req.player.username} added to {join_req.team.name}!")
        elif action == "decline":
            join_req.status = "DECLINED"
            join_req.save()
            messages.info(request, f"Request from {join_req.player.username} declined.")
        return redirect("scrims:team_list")


class ScrimmageListView(LoginRequiredMixin, ListView):
    model = Scrimmage
    template_name = "scrims/scrimmage_list.html"
    context_object_name = "scrimmages"

    def get_queryset(self):
        qs = Scrimmage.objects.select_related("host_team", "opponent_team").order_by("scheduled_at")
        game = self.request.GET.get("game")
        status = self.request.GET.get("status")
        if game:
            qs = qs.filter(host_team__game_title=game)
        if status:
            qs = qs.filter(status=status)
        return qs


class ScrimmageCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Scrimmage
    form_class = ScrimmageForm
    template_name = "scrims/scrimmage_form.html"
    success_url = reverse_lazy("scrims:scrim_list")

    def test_func(self):
        return self.request.user.role in ["MANAGER", "ADMIN"] or self.request.user.is_superuser

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Scrimmage challenge posted to the Scrim Board!")
        return super().form_valid(form)


class ScrimmageUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Scrimmage
    form_class = ScrimmageForm
    template_name = "scrims/scrimmage_form.html"
    success_url = reverse_lazy("scrims:scrim_list")

    def test_func(self):
        scrim = self.get_object()
        return (
            scrim.host_team.manager == self.request.user
            or self.request.user.role in ["ORGANIZER", "ADMIN"]
            or self.request.user.is_superuser
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Scrimmage details updated.")
        return super().form_valid(form)


class ScrimmageAcceptView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Scrimmage
    form_class = ScrimmageAcceptForm
    template_name = "scrims/scrimmage_accept.html"
    success_url = reverse_lazy("scrims:scrim_list")

    def test_func(self):
        return self.request.user.role in ["MANAGER", "ADMIN"] or self.request.user.is_superuser

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["scrimmage"] = self.get_object()
        return kwargs

    def form_valid(self, form):
        form.instance.status = "CONFIRMED"
        messages.success(self.request, "Scrimmage challenge accepted! Match is now confirmed.")
        return super().form_valid(form)


class ScrimmageDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Scrimmage
    template_name = "scrims/scrimmage_confirm_delete.html"
    success_url = reverse_lazy("scrims:scrim_list")

    def test_func(self):
        scrim = self.get_object()
        return (
            scrim.host_team.manager == self.request.user
            or self.request.user.role in ["ORGANIZER", "ADMIN"]
            or self.request.user.is_superuser
        )
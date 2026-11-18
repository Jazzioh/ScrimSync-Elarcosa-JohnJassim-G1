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
        return Team.objects.select_related("manager").prefetch_related(*[f.name for f in Team._meta.many_to_many], "join_requests__player").order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["join_form"] = TeamJoinRequestForm()
        m2m_name = Team._meta.many_to_many[0].name if Team._meta.many_to_many else None
        user_teams = Team.objects.filter(**{m2m_name: self.request.user}) if (m2m_name and self.request.user.is_authenticated) else Team.objects.none()
        context["joined_games"] = set(user_teams.values_list("game_title", flat=True))
        context["joined_team_ids"] = set(user_teams.values_list("id", flat=True))
        m2m_name = Team._meta.many_to_many[0].name if Team._meta.many_to_many else None
        for team in context["teams"]:
            team.active_roster = getattr(team, m2m_name).all() if m2m_name else []
        return context


class TeamCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = "scrims/team_form.html"
    success_url = reverse_lazy("scrims:team_list")

    def test_func(self):
        return self.request.user.role in ["TEAM_MANAGER", "MANAGER", "ADMIN"] or self.request.user.is_superuser

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

    def form_valid(self, form):
        messages.success(self.request, "Squad deleted successfully.")
        return super().form_valid(form)


class TeamJoinRequestCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        m2m_name = Team._meta.many_to_many[0].name
        if request.user in getattr(team, m2m_name).all() or team.manager == request.user:
            messages.warning(request, "You are already part of this team.")
            return redirect("scrims:team_list")
        if Team.objects.filter(**{m2m_name: request.user, "game_title": team.game_title}).exists():
            messages.warning(request, f"You are already on an active {team.get_game_title_display()} roster.")
            return redirect("scrims:team_list")
        if False:
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
            getattr(join_req.team, Team._meta.many_to_many[0].name).add(join_req.player)
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
        return self.request.user.role in ["TEAM_MANAGER", "MANAGER", "ADMIN"] or self.request.user.is_superuser

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
        return self.request.user.role in ["TEAM_MANAGER", "MANAGER", "ADMIN"] or self.request.user.is_superuser

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

    def form_valid(self, form):
        messages.success(self.request, "Scrimmage record cancelled and deleted.")
        return super().form_valid(form)





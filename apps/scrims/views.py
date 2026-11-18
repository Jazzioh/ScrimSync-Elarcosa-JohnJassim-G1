from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User
from .forms import TeamForm
from .models import Team, TeamJoinRequest


class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = "scrims/team_list.html"
    context_object_name = "teams"

    def get_queryset(self):
        user = self.request.user
        pending_qs = TeamJoinRequest.objects.filter(
            status=TeamJoinRequest.Status.PENDING
        ).select_related("player")
        base_qs = Team.objects.select_related("manager").prefetch_related(
            "players",
            Prefetch("join_requests", queryset=pending_qs, to_attr="pending_requests"),
        )
        if user.role == User.Role.TEAM_MANAGER:
            return base_qs.filter(manager=user)
        return base_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == User.Role.PLAYER:
            context["pending_team_ids"] = set(
                TeamJoinRequest.objects.filter(
                    player=self.request.user,
                    status=TeamJoinRequest.Status.PENDING,
                ).values_list("team_id", flat=True)
            )
        else:
            context["pending_team_ids"] = set()
        return context


class TeamCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Role.TEAM_MANAGER, User.Role.ADMIN)
    model = Team
    form_class = TeamForm
    template_name = "scrims/team_form.html"
    success_url = reverse_lazy("scrims:team_list")

    def form_valid(self, form):
        form.instance.manager = self.request.user
        messages.success(self.request, f"Team '{form.instance.name}' created successfully.")
        return super().form_valid(form)


class TeamUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = (User.Role.TEAM_MANAGER, User.Role.ADMIN)
    model = Team
    form_class = TeamForm
    template_name = "scrims/team_form.html"
    success_url = reverse_lazy("scrims:team_list")

    def get_queryset(self):
        if self.request.user.role == User.Role.ADMIN:
            return Team.objects.all()
        return Team.objects.filter(manager=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"Team '{form.instance.name}' updated.")
        return super().form_valid(form)


class TeamDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = (User.Role.TEAM_MANAGER, User.Role.ADMIN)
    model = Team
    template_name = "scrims/team_confirm_delete.html"
    success_url = reverse_lazy("scrims:team_list")

    def get_queryset(self):
        if self.request.user.role == User.Role.ADMIN:
            return Team.objects.all()
        return Team.objects.filter(manager=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"Disbanded team '{self.object.name}'.")
        return super().form_valid(form)


class TeamJoinRequestCreateView(RoleRequiredMixin, View):
    allowed_roles = (User.Role.PLAYER,)

    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        if team.players.filter(pk=request.user.pk).exists():
            messages.info(request, f"You are already on the roster of {team.name}.")
            return redirect("scrims:team_list")

        already_pending = TeamJoinRequest.objects.filter(
            team=team,
            player=request.user,
            status=TeamJoinRequest.Status.PENDING,
        ).exists()
        if already_pending:
            messages.warning(request, f"You already have a pending join request for {team.name}.")
            return redirect("scrims:team_list")

        note = request.POST.get("message", "").strip()[:150]
        TeamJoinRequest.objects.create(team=team, player=request.user, message=note)
        messages.success(request, f"Join request sent to [{team.tag}] {team.name}!")
        return redirect("scrims:team_list")


class TeamJoinRequestRespondView(RoleRequiredMixin, View):
    allowed_roles = (User.Role.TEAM_MANAGER, User.Role.ADMIN)

    def post(self, request, pk):
        join_req = get_object_or_404(
            TeamJoinRequest.objects.select_related("team", "player"),
            pk=pk,
            status=TeamJoinRequest.Status.PENDING,
        )
        if request.user.role != User.Role.ADMIN and join_req.team.manager != request.user:
            messages.error(request, "You do not have permission to review requests for this team.")
            return redirect("scrims:team_list")

        action = request.POST.get("action")
        if action == "accept":
            join_req.status = TeamJoinRequest.Status.ACCEPTED
            join_req.save()
            join_req.team.players.add(join_req.player)
            messages.success(
                request,
                f"Accepted {join_req.player.in_game_name or join_req.player.username} into [{join_req.team.tag}] {join_req.team.name}.",
            )
        elif action == "reject":
            join_req.status = TeamJoinRequest.Status.REJECTED
            join_req.save()
            messages.info(request, f"Declined join request from {join_req.player.username}.")

        return redirect("scrims:team_list")
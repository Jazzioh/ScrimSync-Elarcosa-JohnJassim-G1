from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Team(models.Model):
    class GameTitle(models.TextChoices):
        VALORANT = "VALORANT", "Valorant"
        MLBB = "MLBB", "Mobile Legends: Bang Bang"
        LOL = "LOL", "League of Legends"
        DOTA2 = "DOTA2", "Dota 2"
        CS2 = "CS2", "Counter-Strike 2"

    class SkillTier(models.TextChoices):
        OPEN = "OPEN", "Open / Amateur"
        COLLEGIATE = "COLLEGIATE", "Collegiate Varsity"
        SEMI_PRO = "SEMI_PRO", "Semi-Pro"
        PROFESSIONAL = "PROFESSIONAL", "Professional"

    name = models.CharField(max_length=80, unique=True)
    tag = models.CharField(max_length=10, unique=True, help_text="2-6 character team tag (e.g., CITU)")
    game_title = models.CharField(max_length=20, choices=GameTitle.choices, default=GameTitle.MLBB)
    skill_tier = models.CharField(max_length=20, choices=SkillTier.choices, default=SkillTier.OPEN)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="managed_teams",
    )
    players = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="joined_teams",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"[{self.tag}] {self.name} ({self.get_game_title_display()})"


class TeamJoinRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="join_requests",
    )
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_join_requests",
    )
    message = models.CharField(
        max_length=150,
        blank=True,
        help_text="Optional role/rank note (e.g., EXP / Mythical Immortal)",
    )
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["team", "player"],
                condition=models.Q(status="PENDING"),
                name="unique_pending_team_join_request",
            )
        ]

    def __str__(self) -> str:
        return f"{self.player.username} -> {self.team.tag} ({self.status})"


class Scrimmage(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open Challenge"
        ACCEPTED = "ACCEPTED", "Confirmed / Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Format(models.TextChoices):
        BO1 = "BO1", "Best of 1"
        BO3 = "BO3", "Best of 3"
        BO5 = "BO5", "Best of 5"
        BO7 = "BO7", "Best of 7"

    host_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="hosted_scrims",
    )
    opponent_team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_scrims",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_scrims",
    )
    scheduled_at = models.DateTimeField()
    match_format = models.CharField(max_length=10, choices=Format.choices, default=Format.BO1)
    server_region = models.CharField(max_length=50, default="Asia Pacific")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    notes = models.TextField(blank=True, help_text="Map pool, lobby rules, or Discord contact")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_at"]

    def clean(self):
        if self.opponent_team and self.host_team_id == self.opponent_team_id:
            raise ValidationError("A team cannot schedule a scrimmage against itself.")
        if self.scheduled_at and self.scheduled_at <= timezone.now() and not self.pk:
            raise ValidationError("Scrimmage date and time must be in the future.")

    def __str__(self) -> str:
        opponent = self.opponent_team.tag if self.opponent_team else "TBD"
        return f"{self.host_team.tag} vs {opponent} — {self.scheduled_at:%Y-%m-%d %H:%M}"
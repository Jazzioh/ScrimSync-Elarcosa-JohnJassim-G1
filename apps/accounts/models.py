from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "System Admin"
        TEAM_MANAGER = "TEAM_MANAGER", "Team Manager"
        PLAYER = "PLAYER", "Competitive Player"
        ORGANIZER = "ORGANIZER", "Tournament Organizer"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PLAYER,
    )
    in_game_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Primary IGN or Riot/Steam handle",
    )
    discord_tag = models.CharField(max_length=50, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/",
        blank=True,
        null=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"
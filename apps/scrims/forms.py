from datetime import timedelta
from django import forms
from django.utils import timezone
from .models import Team, TeamJoinRequest, Scrimmage


def _existing_fields(model, candidates):
    model_fields = {f.name for f in model._meta.get_fields()}
    return [f for f in candidates if f in model_fields]


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = _existing_fields(Team, ["name", "tag", "game_title", "description"])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.update({"class": css})


class TeamJoinRequestForm(forms.ModelForm):
    class Meta:
        model = TeamJoinRequest
        fields = _existing_fields(TeamJoinRequest, ["message", "note", "reason"])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control form-control-sm", "placeholder": "Role / IGN note..."})


class ScrimmageForm(forms.ModelForm):
    class Meta:
        model = Scrimmage
        fields = _existing_fields(Scrimmage, ["host_team", "scheduled_at", "server_region", "notes"])
        widgets = {
            "scheduled_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ("scheduled_at", "notes"):
                css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
                field.widget.attrs.update({"class": css})
        if "scheduled_at" in self.fields:
            self.fields["scheduled_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        if "host_team" in self.fields and user and not user.is_superuser and getattr(user, "role", "") != "ADMIN":
            self.fields["host_team"].queryset = Team.objects.filter(manager=user)

    def clean(self):
        cleaned_data = super().clean()
        host_team = cleaned_data.get("host_team")
        scheduled_at = cleaned_data.get("scheduled_at")

        if scheduled_at and scheduled_at <= timezone.now():
            raise forms.ValidationError("Scrimmages cannot be scheduled in the past. Please choose a future date and time.")

        if host_team and scheduled_at:
            window_start = scheduled_at - timedelta(hours=2)
            window_end = scheduled_at + timedelta(hours=2)
            conflict_qs = Scrimmage.objects.filter(
                host_team=host_team,
                scheduled_at__range=(window_start, window_end),
            ).exclude(status="CANCELLED")
            if self.instance.pk:
                conflict_qs = conflict_qs.exclude(pk=self.instance.pk)
            if conflict_qs.exists():
                raise forms.ValidationError(
                    f"{host_team.name} already has a scrimmage scheduled within 2 hours of this time slot."
                )
        return cleaned_data


class ScrimmageAcceptForm(forms.ModelForm):
    class Meta:
        model = Scrimmage
        fields = ["opponent_team"]
        widgets = {
            "opponent_team": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, user=None, scrimmage=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.scrimmage = scrimmage
        if user and scrimmage:
            self.fields["opponent_team"].required = True
            self.fields["opponent_team"].empty_label = "Select your challenging squad..."
            self.fields["opponent_team"].queryset = Team.objects.filter(
                manager=user, game_title=scrimmage.host_team.game_title
            ).exclude(pk=scrimmage.host_team.pk)

    def clean_opponent_team(self):
        opponent = self.cleaned_data.get("opponent_team")
        if not opponent:
            raise forms.ValidationError("Please select one of your squads before accepting this challenge.")
        if self.scrimmage and opponent == self.scrimmage.host_team:
            raise forms.ValidationError("A team cannot accept its own scrimmage challenge.")
        return opponent


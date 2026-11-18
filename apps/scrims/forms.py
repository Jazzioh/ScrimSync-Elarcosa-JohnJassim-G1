from django import forms
from apps.accounts.forms import BootstrapFormMixin
from apps.accounts.models import User
from .models import Team


class TeamForm(BootstrapFormMixin, forms.ModelForm):
    players = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role=User.Role.PLAYER, is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select active Competitive Players for this roster.",
    )

    class Meta:
        model = Team
        fields = ("name", "tag", "game_title", "skill_tier", "players", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["players"].widget.attrs.pop("class", None)

    def clean_tag(self) -> str:
        return self.cleaned_data["tag"].strip().upper()
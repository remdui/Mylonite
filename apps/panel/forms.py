from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError

from .services import (
    clear_login_throttle,
    get_login_lockout,
    register_failed_login_attempt,
)

User = get_user_model()


class StyledFormMixin:
    input_class = "form-input"

    def _append_class(self, widget: forms.Widget, class_name: str) -> None:
        existing = widget.attrs.get("class", "")
        classes = " ".join(part for part in [existing, class_name] if part).strip()
        widget.attrs["class"] = classes

    def _apply_common_widget_attrs(self) -> None:
        for field in self.fields.values():
            self._append_class(field.widget, self.input_class)


class OwnerSetupForm(StyledFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._apply_common_widget_attrs()

        self.fields["username"].label = "Username"
        self.fields[
            "username"
        ].help_text = "This will be the owner account used to access the Mylonite administrative panel."
        self.fields["username"].widget.attrs.update(
            {
                "autocomplete": "username",
                "autofocus": True,
                "placeholder": "Choose a username",
            }
        )

        self.fields["password1"].label = "Password"
        self.fields["password1"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "placeholder": "Create a strong password",
            }
        )

        self.fields["password2"].label = "Repeat password"
        self.fields["password2"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "placeholder": "Repeat the password",
            }
        )

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True

        if commit:
            user.save()

        return user


class PanelAuthenticationForm(StyledFormMixin, AuthenticationForm):
    error_messages = {
        "invalid_login": "Please enter a correct username and password.",
        "inactive": "This account is inactive.",
        "locked": "Too many sign-in attempts. Please wait before trying again.",
    }

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(),
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(),
    )

    def __init__(self, request=None, *args, **kwargs) -> None:
        super().__init__(request=request, *args, **kwargs)
        self._apply_common_widget_attrs()

        self.fields["username"].widget.attrs.update(
            {
                "autocomplete": "username",
                "autofocus": True,
                "placeholder": "Username",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "autocomplete": "current-password",
                "placeholder": "Password",
            }
        )

    def clean(self):
        username = self.data.get("username", "").strip()
        password = self.data.get("password", "")

        if username:
            lockout = get_login_lockout(self.request, username)
            if lockout.is_locked:
                raise ValidationError(
                    self.error_messages["locked"],
                    code="locked",
                )

        try:
            cleaned_data = super().clean()
        except ValidationError:
            if username and password:
                register_failed_login_attempt(self.request, username)
            raise

        if username:
            clear_login_throttle(self.request, username)

        return cleaned_data


class PanelPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    def __init__(self, user, *args, **kwargs) -> None:
        super().__init__(user, *args, **kwargs)
        self._apply_common_widget_attrs()

        self.fields["old_password"].label = "Current password"
        self.fields["old_password"].widget.attrs.update(
            {
                "autocomplete": "current-password",
                "placeholder": "Current password",
            }
        )

        self.fields["new_password1"].label = "New password"
        self.fields["new_password1"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "placeholder": "New password",
            }
        )

        self.fields["new_password2"].label = "Repeat new password"
        self.fields["new_password2"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "placeholder": "Repeat new password",
            }
        )


class ThemeSelectionForm(StyledFormMixin, forms.Form):
    theme_name = forms.ChoiceField(
        label="Theme",
        choices=(),
    )

    def __init__(
        self,
        *args,
        theme_choices: list[tuple[str, str]] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.fields["theme_name"].choices = theme_choices or []
        self._apply_common_widget_attrs()

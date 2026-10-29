from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=256, widget=forms.TextInput(attrs={"type": "text"}))
    last_name = forms.CharField(required=True, max_length=256, widget=forms.TextInput(attrs={"type": "text"}))
    email = forms.EmailField(required=True, max_length=256,help_text="We will not share your email", widget=forms.EmailInput(attrs={"type": "email"}))
    username = forms.CharField(required=True, max_length=150,help_text="Make sure to choose unique username", widget=forms.TextInput(attrs={"type": "text"}))

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "username", "password1", "password2")

    # ==========================================
    # FIELDS VALIDATIONS
    # ==========================================

    def clean_email(self):
        # Get the email, strip whitespace, and make it lowercase
        email = self.cleaned_data.get('email', '').strip().lower()

        # Check if email already exists in the database (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")

        return email

    def clean_username(self):
        # Get the username and strip whitespace
        username = self.cleaned_data.get('username', '').strip()

        # Check if username already exists in the database (case-insensitive)
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists.")

        return username




class LoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        max_length=256,
        widget=forms.EmailInput(attrs={"type": "email", "placeholder": "Email Address"})
    )

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"type": "password", "placeholder": "Password"})
    )

    def clean_email(self):
        # Strip whitespace and lowercase to match how it was saved during registration
        email = self.cleaned_data.get('email', '').strip().lower()
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            # Authenticate the user.
            # Note: Even though the field is 'email', we pass it as the 'username' kwarg
            # because Django's ModelBackend looks at your model's USERNAME_FIELD.
            user = authenticate(username=email, password=password)

            if user is None:
                # Raise a non-field error if credentials are invalid
                raise forms.ValidationError("Invalid email or password.")

            if not user.is_active:
                raise forms.ValidationError("This account has been deactivated.")

            # Save the user object to cleaned_data so the view can use it
            cleaned_data['user'] = user

        return cleaned_data

class ProfileSettingsForm(forms.ModelForm):
    """Form for editing basic profile information"""

    first_name = forms.CharField(
        max_length=256,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=256,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    bio = forms.CharField(
        max_length=512,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tell us about yourself...', 'rows': 3})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'bio']

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()

        # Check if username is taken by ANOTHER user (exclude current user)
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken.")

        return username


class CustomPasswordChangeForm(PasswordChangeForm):
    """Django's built-in password change form with Bootstrap styling"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

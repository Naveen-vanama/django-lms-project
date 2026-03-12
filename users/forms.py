from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import CustomUser

User = get_user_model()


class LoginForm(AuthenticationForm):
    """Professional login form with username/email/phone login"""

    username = forms.CharField(
        label="Username / Email / Phone",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username, Email or Phone'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")

        # login with email
        if "@" in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass

        # login with phone
        if username.isdigit():
            try:
                user = User.objects.get(phone=username)
                return user.username
            except User.DoesNotExist:
                pass

        return username


class RegisterForm(UserCreationForm):
    """User registration form with approval system."""

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number'
        })
    )

    # 🚫 Remove ADMIN from choices
    role = forms.ChoiceField(
        choices=[
            (CustomUser.Role.STUDENT, 'Student'),
            (CustomUser.Role.INSTRUCTOR, 'Instructor'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'role',
            'password1',
            'password2',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)

        # 🚨 VERY IMPORTANT
        user.is_active = False      # Cannot login
        user.is_approved = False    # Needs admin approval

        if commit:
            user.save()

        return user


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'bio',
                  'date_of_birth', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
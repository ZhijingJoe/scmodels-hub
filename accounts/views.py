from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from .models import EmailVerification


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email is required.')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.email = form.cleaned_data['email']
            user.save()

            # Create verification token
            verification = EmailVerification.objects.create(
                user=user, email=user.email
            )
            verify_url = request.build_absolute_uri(
                f'/accounts/verify/{verification.token}/'
            )

            # Try to send email, fall back to showing link on page
            try:
                send_mail(
                    '[scModels Hub] Verify your email',
                    f'Click to verify: {verify_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request,
                    'Registration successful! Check your email to verify.')
            except Exception:
                # No SMTP configured — show link directly (dev mode)
                messages.success(request,
                    f'Registered! Verify: {verify_url}')

            return render(request, 'accounts/register_done.html', {
                'verify_url': verify_url,
                'email': user.email,
            })
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request, token):
    verification = get_object_or_404(EmailVerification, token=token)
    if not verification.is_verified:
        verification.is_verified = True
        verification.save()
        messages.success(request, 'Email verified! You can now sign in.')
    else:
        messages.info(request, 'Email already verified.')
    return redirect('login')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check email verification
            try:
                v = EmailVerification.objects.get(user=user)
                if not v.is_verified:
                    messages.warning(request,
                        'Please verify your email first. Check your inbox.')
                    return render(request, 'accounts/login.html')
            except EmailVerification.DoesNotExist:
                pass  # Old users without verification record
            login(request, user)
            return redirect(request.GET.get('next', 'index'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('index')

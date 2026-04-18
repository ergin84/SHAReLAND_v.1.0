from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                # Map custom form fields to User model
                user = form.save(commit=False)
                user.email = form.cleaned_data.get('email', '')
                user.first_name = form.cleaned_data.get('name', '')
                user.last_name = form.cleaned_data.get('surname', '')
                user.is_active = False  # 🔒 User must be activated by admin
                user.save()

                # Save profile fields (without name/surname; use User's names)
                profile, created = Profile.objects.get_or_create(user=user)
                profile.affiliation = form.cleaned_data.get('affiliation', '') or None
                profile.orcid = form.cleaned_data.get('orcid', '') or None
                profile.save()

                username = form.cleaned_data.get('username')
                messages.success(request, f'Account created for {username}. Awaiting admin approval.')
                return redirect('login')
            except IntegrityError as e:
                # Handle database integrity errors (duplicate email, username, etc.)
                error_message = str(e)
                if 'email' in error_message.lower() or 'auth_user_email' in error_message.lower():
                    messages.error(request, 'This email address is already registered. Please use a different email or try logging in.')
                elif 'username' in error_message.lower() or 'auth_user_username' in error_message.lower():
                    messages.error(request, 'This username is already taken. Please choose a different username.')
                else:
                    messages.error(request, 'An error occurred during registration. Please try again or contact support if the problem persists.')
                # Re-render the form with the error message
                return render(request, 'users/register.html', {'form': form})
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})



@login_required
def profile(request):
    # Ensure profile exists
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=user_profile)
        u_valid = u_form.is_valid()
        p_valid = p_form.is_valid()

        if u_valid and p_valid:
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
        else:
            if not u_valid:
                for field, errors in u_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field.replace("_", " ").title()}: {error}')
            if not p_valid:
                for field, errors in p_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field.replace("_", " ").title()}: {error}')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=user_profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile.html', context)

"""
Author and user management utilities for ShareLand frontend.
Handles creation and management of Author instances.
"""

import secrets
import string
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from users.models import Profile
from ..models import Author


def get_or_create_author_for_user(user, affiliation=None, orcid=None):
    """
    Get or create Author for a User.
    Updates author information from user profile if available.
    
    Args:
        user: Django User instance
        affiliation: Optional affiliation string
        orcid: Optional ORCID identifier
        
    Returns:
        Author instance
    """
    from django.db import models as django_models
    
    # Try to find existing author linked to this user
    author = Author.objects.filter(user=user).first()
    
    if author:
        # Update author info from profile if available
        try:
            profile = user.profile
            updated = False
            if profile.name and not author.name:
                author.name = profile.name
                updated = True
            if profile.surname and not author.surname:
                author.surname = profile.surname
                updated = True
            if profile.affiliation and not author.affiliation:
                author.affiliation = profile.affiliation
                updated = True
            if profile.orcid and not author.orcid:
                author.orcid = profile.orcid
                updated = True
            if updated:
                author.save()
        except Profile.DoesNotExist:
            pass
        return author
    
    # Also check if author exists by email (user may have not been set initially)
    if user.email:
        author = Author.objects.filter(contact_email=user.email).first()
        if author:
            # Link the user if not already linked
            if not author.user:
                author.user = user
                author.save()
            return author
    
    # Create new Author from user/profile data
    try:
        profile = user.profile
        author = Author.objects.create(
            user=user,
            name=profile.name or user.first_name or '',
            surname=profile.surname or user.last_name or '',
            contact_email=user.email,
            affiliation=affiliation or profile.affiliation or '',
            orcid=orcid or profile.orcid or ''
        )
    except Profile.DoesNotExist:
        author = Author.objects.create(
            user=user,
            name=user.first_name or '',
            surname=user.last_name or '',
            contact_email=user.email,
            affiliation=affiliation or '',
            orcid=orcid or ''
        )
    
    return author


def create_user_and_author(name, surname, email, affiliation=None, orcid=None, send_email=True):
    """
    Create a new User with random password and corresponding Author with mapping.
    Sends email notification with password reset link.
    
    Args:
        name: User's first name
        surname: User's last name
        email: User's email address
        affiliation: Optional affiliation
        orcid: Optional ORCID identifier
        send_email: Whether to send notification email (default True)
        
    Returns:
        Author instance
    """
    # Generate random password
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(16))
    
    # Create username from email or generate unique one
    username = email.split('@')[0] if email else f"{name.lower()}.{surname.lower()}"
    # Ensure username is unique
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=name,
        last_name=surname,
        is_active=True  # User is active but should reset password
    )
    
    # Update profile
    try:
        profile = user.profile
        profile.name = name
        profile.surname = surname
        if affiliation:
            profile.affiliation = affiliation
        if orcid:
            profile.orcid = orcid
        profile.save()
    except Profile.DoesNotExist:
        pass
    
    # Create Author
    author = Author.objects.create(
        user=user,
        name=name,
        surname=surname,
        contact_email=email,
        affiliation=affiliation or '',
        orcid=orcid or ''
    )
    
    # Send email notification
    if send_email:
        send_new_user_notification(user, password)
    
    return author


def find_or_create_author(name, surname, email, affiliation=None, orcid=None):
    """
    Find an existing author by email first, or create a new one.
    
    This prevents duplicate Author records when creating research.
    If an author with this email exists, return it; otherwise create new.
    
    Args:
        name: Author's first name
        surname: Author's last name
        email: Author's email address (used for deduplication)
        affiliation: Optional affiliation
        orcid: Optional ORCID identifier
        
    Returns:
        Author instance
    """
    # First, check if author exists by email
    if email:
        existing = Author.objects.filter(contact_email=email).first()
        if existing:
            # Update fields if provided and missing
            updated = False
            if name and not existing.name:
                existing.name = name
                updated = True
            if surname and not existing.surname:
                existing.surname = surname
                updated = True
            if affiliation and not existing.affiliation:
                existing.affiliation = affiliation
                updated = True
            if orcid and not existing.orcid:
                existing.orcid = orcid
                updated = True
            if updated:
                existing.save()
            return existing
    
    # Check if user exists by email; if so, get/create author for that user
    if email:
        user = User.objects.filter(email=email).first()
        if user:
            return get_or_create_author_for_user(user, affiliation=affiliation, orcid=orcid)
    
    # No existing author or user found, create new author standalone
    author = Author.objects.create(
        name=name or '',
        surname=surname or '',
        contact_email=email or '',
        affiliation=affiliation or '',
        orcid=orcid or ''
    )
    return author


def send_new_user_notification(user, temporary_password):
    """
    Send email notification to new user with temporary password and instructions.
    
    Args:
        user: Django User instance
        temporary_password: Generated temporary password
    """
    try:
        subject = 'Welcome to SHAReLAND - Account Created'
        
        # Prepare email context
        context = {
            'user': user,
            'username': user.username,
            'temporary_password': temporary_password,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Render HTML and plain text versions
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">Welcome to SHAReLAND</h1>
                </div>
                
                <div style="background: #f5f6fa; padding: 30px; border-radius: 0 0 8px 8px;">
                    <p>Hello <strong>{user.first_name} {user.last_name}</strong>,</p>
                    
                    <p>Your account has been created on SHAReLAND as a research author. You can now access the platform to manage your research projects.</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #3498db;">
                        <h3 style="margin-top: 0; color: #2c3e50;">Your Login Credentials</h3>
                        <p style="margin: 10px 0;"><strong>Username:</strong> {user.username}</p>
                        <p style="margin: 10px 0;"><strong>Temporary Password:</strong> <code style="background: #ecf0f1; padding: 5px 10px; border-radius: 4px; font-family: monospace;">{temporary_password}</code></p>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #f39c12;">
                        <p style="margin: 0;"><strong>⚠️ Important Security Notice:</strong></p>
                        <p style="margin: 10px 0 0 0;">For security reasons, we strongly recommend changing your password after your first login. You can also use the "Forgot Password" feature to set a new password immediately.</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{context['site_url']}/login/" style="display: inline-block; background: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold;">Login to SHAReLAND</a>
                    </div>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <p style="margin: 5px 0;">or</p>
                        <a href="{context['site_url']}/password_reset/" style="color: #3498db; text-decoration: none;">Reset Your Password Now</a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="font-size: 14px; color: #7f8c8d;">
                        If you did not expect this email or have any questions, please contact the research administrator who added you to the project.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
Welcome to SHAReLAND

Hello {user.first_name} {user.last_name},

Your account has been created on SHAReLAND as a research author. You can now access the platform to manage your research projects.

Your Login Credentials:
-----------------------
Username: {user.username}
Temporary Password: {temporary_password}

IMPORTANT SECURITY NOTICE:
For security reasons, we strongly recommend changing your password after your first login. You can also use the "Forgot Password" feature to set a new password immediately.

Login: {context['site_url']}/login/
Reset Password: {context['site_url']}/password_reset/

If you did not expect this email or have any questions, please contact the research administrator who added you to the project.

Best regards,
The SHAReLAND Team
        """
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        print(f"Failed to send email to {user.email}: {str(e)}")
        return False

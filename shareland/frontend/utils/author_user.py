"""
Simplified author management using User as the single source of truth.
After consolidating Author table into User/Profile, use these utilities.
"""

from django.contrib.auth.models import User
from users.models import Profile


def get_or_update_user_profile(user, affiliation=None, orcid=None, contact_email=None):
    """
    Ensure a User has a Profile with author fields populated.
    Useful after consolidating Author table.
    
    Args:
        user: Django User instance
        affiliation: Optional affiliation to set on Profile
        orcid: Optional ORCID to set on Profile
        contact_email: Optional contact email to set on Profile
        
    Returns:
        User instance (with related Profile ensured to exist)
    """
    profile, created = Profile.objects.get_or_create(user=user)
    updated = False
    
    if affiliation and not profile.affiliation:
        profile.affiliation = affiliation
        updated = True
    if orcid and not profile.orcid:
        profile.orcid = orcid
        updated = True
    if contact_email and not profile.contact_email:
        profile.contact_email = contact_email
        updated = True
    
    if updated or created:
        profile.save()
    
    return user


def find_or_create_user_as_author(name, surname, email, affiliation=None, orcid=None, send_email=False):
    """
    Find an existing User by email, or create a new one to serve as an author.
    Single source of truth: Users are authors.
    
    Args:
        name: First name
        surname: Last name
        email: Email address (used for lookup/creation)
        affiliation: Optional affiliation
        orcid: Optional ORCID
        send_email: Whether to send welcome email (not implemented here; add if needed)
        
    Returns:
        User instance with Profile ensured
    """
    # Check if user exists by email
    user = User.objects.filter(email=email).first()
    if user:
        return get_or_update_user_profile(user, affiliation=affiliation, orcid=orcid, contact_email=email)
    
    # Create new user from author data
    # Generate unique username from email or name
    base_username = email.split('@')[0] if email else f'{name.lower()}.{surname.lower()}'
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base_username}{counter}'
        counter += 1
    
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=name or '',
        last_name=surname or '',
        is_active=False  # Not active until they register/confirm
    )
    
    # Ensure profile exists and populate author fields
    get_or_update_user_profile(user, affiliation=affiliation, orcid=orcid, contact_email=email)
    
    return user

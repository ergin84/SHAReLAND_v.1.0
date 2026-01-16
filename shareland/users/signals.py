from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, created, **kwargs):
    if not created:  # Only save profile if user already exists (not newly created)
        # Check if profile exists before trying to save it
        if Profile.objects.filter(user=instance).exists():
            try:
                instance.profile.save()
            except Exception:
                # If save fails, skip silently
                pass
        else:
            # Profile doesn't exist, create it
            Profile.objects.get_or_create(user=instance)
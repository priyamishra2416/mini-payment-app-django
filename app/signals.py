from django.db.models.signals import post_migrate, post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from .models import Wallet


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)


@receiver(post_migrate)
def ensure_default_admin(sender, **kwargs):
    if sender.name != 'app':
        return

    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@pocketpay.local',
            password='admin123',
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save(update_fields=['is_staff', 'is_superuser'])
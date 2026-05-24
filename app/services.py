from .models import Wallet


def ensure_default_admin_user():
	from django.contrib.auth.models import User

	admin_user, created = User.objects.get_or_create(
		username='admin',
		defaults={'email': 'admin@pocketpay.local'},
	)
	if created or not admin_user.check_password('admin123'):
		admin_user.set_password('admin123')
		admin_user.email = 'admin@pocketpay.local'
		admin_user.is_staff = True
		admin_user.is_superuser = True
		admin_user.save()
	return admin_user


def ensure_wallet(user):
	wallet, _ = Wallet.objects.get_or_create(user=user)
	return wallet
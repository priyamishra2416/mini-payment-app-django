import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class Wallet(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
	balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('5000.00'))
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'{self.user.username} wallet'


class Transaction(models.Model):
	class Status(models.TextChoices):
		SUCCESS = 'success', 'Success'
		FAILED = 'failed', 'Failed'

	sender = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='sent_transactions',
	)
	receiver = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='received_transactions',
	)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	transaction_id = models.CharField(max_length=32, unique=True, editable=False)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUCCESS)
	timestamp = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		if not self.transaction_id:
			self.transaction_id = f'PP-{uuid.uuid4().hex[:12].upper()}'
		super().save(*args, **kwargs)

	def __str__(self):
		return self.transaction_id

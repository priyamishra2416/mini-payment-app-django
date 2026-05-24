from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Transaction, Wallet


class PocketPaySmokeTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.sender = User.objects.create_user(username='alice', email='alice@example.com', password='Pass12345!')
		self.receiver = User.objects.create_user(username='bob', email='bob@example.com', password='Pass12345!')

	def test_register_login_logout_flow(self):
		response = self.client.post(
			reverse('register'),
			{
				'username': 'charlie',
				'email': 'charlie@example.com',
				'password1': 'Pass12345!',
				'password2': 'Pass12345!',
			},
		)
		self.assertRedirects(response, reverse('login'))
		user = User.objects.get(username='charlie')
		self.assertTrue(Wallet.objects.filter(user=user).exists())

		logged_in = self.client.login(username='charlie', password='Pass12345!')
		self.assertTrue(logged_in)
		response = self.client.get(reverse('dashboard'))
		self.assertEqual(response.status_code, 200)

		response = self.client.get(reverse('logout'))
		self.assertRedirects(response, reverse('login'))

	def test_register_password_mismatch_message(self):
		response = self.client.post(
			reverse('register'),
			{
				'username': 'dana',
				'email': 'dana@example.com',
				'password1': 'Pass12345!',
				'password2': 'Pass1234!',
			},
			follow=True,
		)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Password mismatch')

	def test_default_admin_login_works(self):
		response = self.client.post(
			reverse('login'),
			{'username': 'admin', 'password': 'admin123'},
		)
		self.assertRedirects(response, reverse('dashboard'))
		self.assertTrue(User.objects.filter(username='admin').exists())

	def test_csrf_tokens_present_on_auth_and_transfer_pages(self):
		anonymous_client = Client()
		response = anonymous_client.get(reverse('login'))
		self.assertContains(response, 'csrfmiddlewaretoken')
		response = anonymous_client.get(reverse('register'))
		self.assertContains(response, 'csrfmiddlewaretoken')
		self.client.login(username='alice', password='Pass12345!')
		response = self.client.get(reverse('send_money'))
		self.assertContains(response, 'csrfmiddlewaretoken')

	def test_send_money_updates_balances_and_history(self):
		self.client.login(username='alice', password='Pass12345!')
		response = self.client.get(reverse('send_money'))
		token = response.context['form'].initial['submission_token']

		response = self.client.post(
			reverse('send_money'),
			{'receiver': self.receiver.id, 'amount': '125.50', 'submission_token': token},
		)
		self.assertEqual(response.status_code, 302)
		transaction = Transaction.objects.get()
		self.assertRedirects(response, reverse('receipt', kwargs={'transaction_id': transaction.transaction_id}), fetch_redirect_response=False)

		self.sender.refresh_from_db()
		self.receiver.refresh_from_db()
		self.assertEqual(self.sender.wallet.balance, Decimal('4874.50'))
		self.assertEqual(self.receiver.wallet.balance, Decimal('5125.50'))

		receipt = self.client.get(reverse('receipt', kwargs={'transaction_id': transaction.transaction_id}))
		self.assertEqual(receipt.status_code, 200)

		duplicate = self.client.post(
			reverse('send_money'),
			{'receiver': self.receiver.id, 'amount': '125.50', 'submission_token': token},
			follow=True,
		)
		self.assertContains(duplicate, 'Duplicate submission detected')
		self.assertEqual(Transaction.objects.count(), 1)

	def test_history_profile_qr_pages_render(self):
		self.client.login(username='alice', password='Pass12345!')
		for url_name in ('dashboard', 'profile', 'qr_payment', 'history'):
			response = self.client.get(reverse(url_name))
			self.assertEqual(response.status_code, 200)

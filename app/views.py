from decimal import Decimal
import uuid

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LoginForm, RegistrationForm, SendMoneyForm, TransactionSearchForm
from .models import Transaction, Wallet
from .services import ensure_default_admin_user, ensure_wallet


def login_view(request):
	if request.user.is_authenticated:
		return redirect('dashboard')

	ensure_default_admin_user()

	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			user = authenticate(request, username=username, password=password)
			if user is not None:
				login(request, user)
				messages.success(request, 'Login successful')
				return redirect('dashboard')
			messages.error(request, 'Invalid credentials')
	else:
		form = LoginForm()

	return render(request, 'login.html', {'form': form})


def register_view(request):
	if request.user.is_authenticated:
		return redirect('dashboard')

	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		email = request.POST.get('email', '').strip()
		password1 = request.POST.get('password1', '')
		password2 = request.POST.get('password2', '')

		if not username or not email or not password1 or not password2:
			messages.error(request, 'All fields are required')
			return redirect('register')

		if password1 != password2:
			messages.error(request, 'Password mismatch')
			return redirect('register')

		if User.objects.filter(username=username).exists():
			messages.error(request, 'Username already exists')
			return redirect('register')

		if User.objects.filter(email=email).exists():
			messages.error(request, 'Email already exists')
			return redirect('register')

		user = User.objects.create_user(
			username=username,
			email=email,
			password=password1,
		)
		ensure_wallet(user)
		messages.success(request, 'Account created successfully')
		return redirect('login')
	else:
		form = RegistrationForm()

	return render(request, 'register.html', {'form': form})


def logout_view(request):
	logout(request)
	messages.success(request, 'You have been logged out.')
	return redirect('login')


@login_required(login_url='login')
def dashboard(request):
	wallet = ensure_wallet(request.user)
	counterparties = (
		User.objects.filter(Q(sent_transactions__receiver=request.user) | Q(received_transactions__sender=request.user))
		.exclude(id=request.user.id)
		.distinct()
		.order_by('username')[:4]
	)
	sent_total = Transaction.objects.filter(sender=request.user, status=Transaction.Status.SUCCESS).aggregate(
		total=Sum('amount')
	)['total'] or Decimal('0.00')
	received_total = Transaction.objects.filter(receiver=request.user, status=Transaction.Status.SUCCESS).aggregate(
		total=Sum('amount')
	)['total'] or Decimal('0.00')
	recent_transactions = (
		Transaction.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
		.select_related('sender', 'receiver')
		.order_by('-timestamp')[:5]
	)
	last_transaction = recent_transactions[0] if recent_transactions else None
	wallet_status = 'Active' if wallet.balance > 0 else 'Low balance'
	return render(
		request,
		'dashboard.html',
		{
			'wallet': wallet,
			'sent_total': sent_total,
			'received_total': received_total,
			'recent_transactions': recent_transactions,
			'counterparties': counterparties,
			'last_transaction': last_transaction,
			'wallet_status': wallet_status,
			'active_account': request.user.username,
		},
	)


@login_required(login_url='login')
def staff_dashboard_view(request):
	if not request.user.is_staff:
		return redirect('dashboard')

	total_users = User.objects.count()
	total_transactions = Transaction.objects.count()
	total_money_transferred = Transaction.objects.filter(status=Transaction.Status.SUCCESS).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
	recent_payments = Transaction.objects.select_related('sender', 'receiver').order_by('-timestamp')[:8]
	return render(
		request,
		'staff_dashboard.html',
		{
			'total_users': total_users,
			'total_transactions': total_transactions,
			'total_money_transferred': total_money_transferred,
			'recent_payments': recent_payments,
		},
	)


@login_required(login_url='login')
def profile_view(request):
	wallet = ensure_wallet(request.user)
	total_transactions = Transaction.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).count()
	return render(request, 'profile.html', {'wallet': wallet, 'total_transactions': total_transactions})


@login_required(login_url='login')
def send_money_view(request):
	ensure_wallet(request.user)
	if not User.objects.exclude(id=request.user.id).exists():
		messages.warning(request, 'No other users are available yet.')

	if request.method == 'POST':
		form = SendMoneyForm(request.POST, user=request.user)
		if form.is_valid():
			receiver = form.cleaned_data['receiver']
			amount = form.cleaned_data['amount']
			submission_token = form.cleaned_data['submission_token']

			if request.session.get('send_money_token') != submission_token:
				messages.error(request, 'Duplicate submission detected. Please try again.')
				return redirect('send_money')

			try:
				with db_transaction.atomic():
					sender_wallet = Wallet.objects.select_for_update().get(user=request.user)
					receiver_wallet = Wallet.objects.select_for_update().get_or_create(user=receiver)[0]

					if amount <= 0:
						messages.error(request, 'Invalid transfer amount.')
						return redirect('send_money')

					if receiver == request.user:
						messages.error(request, 'You cannot send money to yourself.')
						return redirect('send_money')

					if sender_wallet.balance < amount:
						messages.error(request, 'Insufficient balance.')
						return redirect('send_money')

					sender_wallet.balance -= amount
					receiver_wallet.balance += amount
					sender_wallet.save(update_fields=['balance'])
					receiver_wallet.save(update_fields=['balance'])

					transaction = Transaction.objects.create(
						sender=request.user,
						receiver=receiver,
						amount=amount,
						status=Transaction.Status.SUCCESS,
					)

					request.session['send_money_token'] = uuid.uuid4().hex

				messages.success(request, f'Sent {amount} to {receiver.username}.')
				return redirect('receipt', transaction_id=transaction.transaction_id)
			except Exception:
				messages.error(request, 'Transfer failed. Please try again.')
	else:
		form = SendMoneyForm(user=request.user)
		request.session['send_money_token'] = uuid.uuid4().hex
		form.initial['submission_token'] = request.session['send_money_token']

	return render(request, 'send_money.html', {'form': form})


@login_required(login_url='login')
def receipt_view(request, transaction_id):
	transaction = get_object_or_404(Transaction.objects.select_related('sender', 'receiver'), transaction_id=transaction_id)
	if request.user not in (transaction.sender, transaction.receiver):
		return redirect('dashboard')
	return render(request, 'receipt.html', {'transaction': transaction})


@login_required(login_url='login')
def qr_payment_view(request):
	payment_id = f'PPOCKET-{request.user.username.upper()}-{request.user.id}'
	return render(request, 'qr_payment.html', {'payment_id': payment_id, 'wallet': ensure_wallet(request.user)})


@login_required(login_url='login')
def history_view(request):
	search_form = TransactionSearchForm(request.GET or None)
	query = request.GET.get('query', '').strip()
	direction = request.GET.get('direction', 'all')
	status = request.GET.get('status', 'all')

	base_queryset = Transaction.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).select_related('sender', 'receiver')

	if query:
		base_queryset = base_queryset.filter(
			Q(transaction_id__icontains=query)
			| Q(sender__username__icontains=query)
			| Q(receiver__username__icontains=query)
		)

	if status in ('success', 'failed'):
		base_queryset = base_queryset.filter(status=status)

	sent_transactions = base_queryset.filter(sender=request.user).order_by('-timestamp')
	received_transactions = base_queryset.filter(receiver=request.user).order_by('-timestamp')

	if direction == 'sent':
		all_transactions = sent_transactions
	elif direction == 'received':
		all_transactions = received_transactions
	else:
		all_transactions = base_queryset.order_by('-timestamp')

	return render(
		request,
		'history.html',
		{
			'search_form': search_form,
			'sent_transactions': sent_transactions,
			'received_transactions': received_transactions,
			'all_transactions': all_transactions,
			'current_query': query,
			'current_direction': direction,
			'current_status': status,
		},
	)

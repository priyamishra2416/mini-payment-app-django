from .services import ensure_wallet


def wallet_context(request):
	if not request.user.is_authenticated:
		return {'wallet': None, 'wallet_balance': '0.00'}

	wallet = ensure_wallet(request.user)
	return {'wallet': wallet, 'wallet_balance': wallet.balance}
from django.contrib import admin

from .models import Transaction, Wallet

admin.site.site_header = 'PocketPay Administration'
admin.site.site_title = 'PocketPay Admin'
admin.site.index_title = 'Fintech Control Center'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
	list_display = ('user', 'balance', 'created_at')
	search_fields = ('user__username',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
	list_display = ('transaction_id', 'sender', 'receiver', 'amount', 'status', 'timestamp')
	list_filter = ('status', 'timestamp')
	search_fields = ('transaction_id', 'sender__username', 'receiver__username')

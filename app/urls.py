from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('staff-dashboard/', views.staff_dashboard_view, name='staff_dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('send-money/', views.send_money_view, name='send_money'),
    path('receipt/<str:transaction_id>/', views.receipt_view, name='receipt'),
    path('qr-payment/', views.qr_payment_view, name='qr_payment'),
    path('history/', views.history_view, name='history'),
]
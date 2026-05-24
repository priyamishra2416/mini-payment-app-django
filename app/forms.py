from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class SendMoneyForm(forms.Form):
    receiver = forms.ModelChoiceField(queryset=User.objects.none(), widget=forms.Select(attrs={'class': 'form-select'}))
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('1.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter amount'}),
    )
    submission_token = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['receiver'].queryset = User.objects.exclude(id=user.id).order_by('username')

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']
        if self.user and receiver == self.user:
            raise forms.ValidationError('You cannot send money to yourself.')
        return receiver

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount

    def clean_submission_token(self):
        token = self.cleaned_data['submission_token']
        if not token:
            raise forms.ValidationError('Invalid submission token.')
        return token


class TransactionSearchForm(forms.Form):
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by ID or username'}))
    direction = forms.ChoiceField(
        required=False,
        choices=(
            ('all', 'All'),
            ('sent', 'Sent'),
            ('received', 'Received'),
        ),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=(
            ('all', 'All Statuses'),
            ('success', 'Successful Payments'),
            ('failed', 'Failed Payments'),
        ),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
import datetime
import json
import pytz

from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase
from flowback_addon.ledger.models import Account, Transaction

from flowback.user.models import User


class AccountListAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@user.com', username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_account_list_api(self):
        url = reverse('api:addon:ledger:accounts_list') + '?id=1'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_account_list_api_error(self):
        url = reverse('api:addon:ledger:accounts_list') + '?invalid_param=1'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_account_list_api_empty(self):
        url = reverse('api:addon:ledger:accounts_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_account_list_api_invalid_query_param(self):
        url = reverse('api:addon:ledger:accounts_list') + '?id=abc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_account_list_api_invalid_orderby_param(self):
        url = reverse('api:addon:ledger:accounts_list') + '?id=invalid_param'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AccountCreateAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@user.com', username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_account_create_api(self):
        url = reverse('api:addon:ledger:accounts_create')
        data = {'account_number': '123456789', 'account_name': 'Test Account'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Account.objects.count(), 1)
        account = Account.objects.first()
        self.assertEqual(account.account_number, data['account_number'])
        self.assertEqual(account.account_name, data['account_name'])

    def test_account_create_api_with_error(self):
        url = reverse('api:addon:ledger:accounts_create')
        data = {'account_number': '123456789'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Account.objects.count(), 0)


class AccountUpdateApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@user.com', username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            account_number='123456789', account_name='Test Account', user=self.user)

    def test_account_update_api(self):
        url = reverse('api:addon:ledger:accounts_update',
                      args=[self.account.id])
        payload = {'account_number': '987654321',
                   'account_name': 'Updated Account'}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Account.objects.get(
            id=self.account.id).account_name, payload['account_name'])
        self.assertEqual(Account.objects.get(
            id=self.account.id).account_number, payload['account_number'])

    def test_account_update_api_missing_fields(self):
        url = reverse('api:addon:ledger:accounts_update',
                      args=[self.account.id])
        payload = {'account_number': '123456789'}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Account.objects.get(
            id=self.account.id).account_name, 'Test Account')

    def test_account_update_api_invalid_id(self):
        url = reverse('api:addon:ledger:accounts_update', args=[999])
        payload = {'account_number': '987654321',
                   'account_name': 'Updated Account'}
        response = self.client.post(url, payload)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_json['detail'][0], 'account does not exist')

    def test_account_update_api_empty_payload(self):
        url = reverse('api:addon:ledger:accounts_update',
                      args=[self.account.id])
        payload = {}
        response = self.client.post(url, payload)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Account.objects.get(
            id=self.account.id).account_name, 'Test Account')
        self.assertEqual(
            response_json['detail']['account_number'][0], 'This field is required.')
        self.assertEqual(
            response_json['detail']['account_name'][0], 'This field is required.')

    def test_account_update_api_with_other_user(self):
        other_user = User.objects.create_user(
            email='test2@user.com', username='testuser2', password='testpass')
        self.client.force_authenticate(user=other_user)
        url = reverse('api:addon:ledger:accounts_update',
                      args=[self.account.id])
        payload = {'account_number': '987654321',
                   'account_name': 'Updated Account'}
        response = self.client.post(url, payload)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_json['detail']['non_field_errors'][0], 'Account doesn\'t belong to User')


class AccountDeleteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@user.com', username='testuser', password='testpass')
        self.account = Account.objects.create(
            account_number='123456789', account_name='Test Account', user=self.user)
        self.client.force_authenticate(user=self.user)

    def test_account_delete_api(self):
        url = reverse('api:addon:ledger:accounts_delete',
                      args=[self.account.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Account.objects.filter(id=self.account.id).exists())

    def test_account_delete_api_invalid_id(self):
        url = reverse('api:addon:ledger:accounts_delete', args=[999])
        response = self.client.post(url)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_json['detail'][0], 'account does not exist')

    def test_account_delete_api_with_other_user(self):
        other_user = User.objects.create_user(
            email='test2@user.com', username='testuser2', password='testpass')
        self.client.force_authenticate(user=other_user)
        url = reverse('api:addon:ledger:accounts_delete',
                      args=[self.account.id])
        response = self.client.post(url)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_json['detail']['non_field_errors'][0], "Account doesn\'t belong to User")


class TransactionListAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@user.com', username='testuser', password='testpass')
        self.account = Account.objects.create(
            account_number='123456789', account_name='Test Account', user=self.user)
        self.client.force_authenticate(user=self.user)

    def test_transaction_list_api(self):
        url = reverse('api:addon:ledger:transactions_list',
                      args=[self.account.id]) + '?id=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_account_list_api_error(self):
        url = reverse('api:addon:ledger:transactions_list',
                      args=[self.account.id]) + '?invalid_param=1'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_account_list_api_empty(self):
        url = reverse('api:addon:ledger:transactions_list',
                      args=[self.account.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_account_list_api_invalid_query_param(self):
        url = reverse('api:addon:ledger:transactions_list',
                      args=[self.account.id]) + '?id=abc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_account_list_api_invalid_orderby_param(self):
        url = reverse('api:addon:ledger:transactions_list',
                      args=[self.account.id]) + '?id=invalid_param'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TransactionCreateAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@user.com', username='testuser', password='testpass')
        self.account = Account.objects.create(
            account_number='123456789', account_name='Test Account', user=self.user)
        self.client.force_authenticate(user=self.user)

    def test_transaction_create_api(self):
        url = reverse('api:addon:ledger:transactions_create',
                      args=[self.account.id])
        data = {
            'description': 'Test transaction',
            'verification_number': '123',
            'credit_amount': 20,
            'date': datetime.datetime.now()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.description, data['description'])
        self.assertEqual(transaction.verification_number,
                         data['verification_number'])
        self.assertEqual(transaction.credit_amount, data['credit_amount'])

    def test_transaction_create_api_with_error(self):
        url = reverse('api:addon:ledger:transactions_create',
                      args=[self.account.id])
        data = {
            'description': 'Test transaction',
            'verification_number': '123',
            'credit_amount': 20,
            'debit_amount': 20,
            'date': datetime.datetime.now()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.count(), 0)


class TransactionUpdateApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@user.com', username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            account_number='123456789', account_name='Test Account', user=self.user)
        self.transaction = Transaction.objects.create(
            description='Test transaction',
            verification_number='123',
            credit_amount=20,
            debit_amount=0,
            date=datetime.datetime.now(pytz.utc),
            account=self.account)

    def test_transaction_update_api(self):
        url = reverse('api:addon:ledger:transactions_update',
                      args=[self.account.id, self.transaction.id])
        payload = {
            'description': 'Update transaction',
            'verification_number': '123',
            'debit_amount': 5,
            'date': datetime.datetime.now(pytz.utc)
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Transaction.objects.get(
            id=self.transaction.id, account_id=self.account.id).description, payload['description'])
        self.assertEqual(Transaction.objects.get(
            id=self.transaction.id).verification_number, payload['verification_number'])
        self.assertEqual(Transaction.objects.get(
            id=self.transaction.id).debit_amount, payload['debit_amount'])
        self.assertEqual(Transaction.objects.get(
            id=self.transaction.id).credit_amount, 0)

    def test_transaction_update_api_missing_fields(self):
        url = reverse('api:addon:ledger:transactions_update',
                      args=[self.account.id, self.transaction.id])
        payload = {'description': 'Update transaction',
            'verification_number': '123',}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Transaction.objects.get(
            id=self.transaction.id).description, 'Test transaction')

    def test_transaction_update_api_invalid_id(self):
        url = reverse('api:addon:ledger:transactions_update', args=[self.account.id, 999])
        payload = {
            'description': 'Update transaction',
            'verification_number': '123',
            'debit_amount': 5,
            'date': datetime.datetime.now(pytz.utc)
        }
        response = self.client.post(url, payload)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_json['detail'][0], 'transaction does not exist')

    def test_transaction_update_api_empty_payload(self):
        url = reverse('api:addon:ledger:transactions_update',
                      args=[self.account.id, self.transaction.id])
        payload = {}
        response = self.client.post(url, payload)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Account.objects.get(
            id=self.account.id).account_name, 'Test Account')
        self.assertEqual(
            response_json['detail']['description'][0], 'This field is required.')
        self.assertEqual(
            response_json['detail']['verification_number'][0], 'This field is required.')

    def test_account_update_api_with_other_user(self):
        other_user = User.objects.create_user(
            email='test2@user.com', username='testuser2', password='testpass')
        self.client.force_authenticate(user=other_user)
        url = reverse('api:addon:ledger:transactions_update',
                      args=[self.account.id, self.transaction.id])
        payload = {
            'description': 'Update transaction',
            'verification_number': '123',
            'debit_amount': 5,
            'date': datetime.datetime.now(pytz.utc)
        }
        response = self.client.post(url, payload)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_json['detail']['non_field_errors'][0], "Account doesn\'t belong to User")
        
    def test_transaction_update_api_with_debit_and_credit_amount(self):
        url = reverse('api:addon:ledger:transactions_update',
                      args=[self.account.id, self.transaction.id])
        data = {
            'description': 'Update transaction',
            'verification_number': '123',
            'credit_amount': 20,
            'debit_amount': 20,
            'date': datetime.datetime.now()
        }
        response = self.client.post(url, data)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_json['detail']['non_field_errors'][0], 'Each transaction must have either a debit or a credit amount, but not both')

class TransactionDeleteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@user.com', username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.account = Account.objects.create(
            account_number='123456789', account_name='Test Account', user=self.user)
        self.transaction = Transaction.objects.create(
            description='Test transaction',
            verification_number='123',
            credit_amount=20,
            debit_amount=0,
            date=datetime.datetime.now(pytz.utc),
            account=self.account)

    def test_transaction_delete_api(self):
        url = reverse('api:addon:ledger:transactions_delete',
                      args=[self.account.id, self.transaction.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Transaction.objects.filter(id=self.transaction.id).exists())

    def test_transaction_delete_api_invalid_id(self):
        self.client.force_login(self.user)
        url = reverse('api:addon:ledger:transactions_delete', args=[self.account.id, 999])
        response = self.client.post(url)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_json['detail'][0], 'transaction does not exist')

    def test_transaction_delete_api_with_other_user(self):
        other_user = User.objects.create_user(
            email='test2@user.com', username='testuser2', password='testpass')
        self.client.force_authenticate(user=other_user)
        url = reverse('api:addon:ledger:transactions_delete',
                      args=[self.account.id, self.transaction.id])
        response = self.client.post(url)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_json['detail']['non_field_errors'][0], 'Account doesn\'t belong to User')


from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from decimal import Decimal
from io import StringIO
from .models import Account

class AccountTransferViewsTestCase(TestCase):

    def setUp(self):
        # Set up some initial data
        self.account1 = Account.objects.create(account_number='123', account_name='Alice', balance=1000)
        self.account2 = Account.objects.create(account_number='456', account_name='Bob', balance=500)

    def test_import_accounts_valid_file(self):
        """Test importing a valid CSV file."""
        csv_data = "ID,Name,Balance\n123,Alice,1000\n456,Bob,500\n"
        csv_file = SimpleUploadedFile("accounts.csv", csv_data.encode(), content_type="text/csv")
        
        # Post the CSV file to the import_accounts view
        response = self.client.post(reverse('import_accounts'), {'csv_file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, 200)
        
        # Check messages
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[-1]), "Successfully processed 2 accounts.")

    def test_import_accounts_invalid_csv_format(self):
            """Test importing a CSV with incorrect headers."""
            csv_data = "ID,Name,Amount\n123,Alice,1000\n456,Bob,500\n"
            csv_file = SimpleUploadedFile("accounts.csv", csv_data.encode(), content_type="text/csv")
            
            # Post the invalid CSV file
            response = self.client.post(reverse('import_accounts'), {'csv_file': csv_file}, format='multipart')
            
            self.assertEqual(response.status_code, 302)
            
            # Check messages
            messages = list(get_messages(response.wsgi_request))
            self.assertEqual(str(messages[-1]), "Invalid CSV format. Expected headers: ID, Name, Balance.")

    def test_list_all_accounts(self):
        """Test that the view returns all accounts."""
        response = self.client.get(reverse('list_accounts'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice')
        self.assertContains(response, 'Bob')

    def test_get_account_info(self):
        """Test retrieving account info by account number."""
        response = self.client.get(reverse('account_detail', kwargs={'account_number': self.account1.account_number}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.account1.account_name)
        self.assertContains(response, str(self.account1.balance))

    def test_transfer_funds_invalid_input(self):
        """Test for invalid transfer (missing fields, insufficient balance)."""
        response = self.client.post(reverse('transfer_funds'), {'from_account': '123', 'to_account': '456', 'amount': ''})
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[-1]), "Please fill in all fields.")

        # Transfer amount exceeding balance
        response = self.client.post(reverse('transfer_funds'), {'from_account': '123', 'to_account': '456', 'amount': '1500'})
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[-1]), "Insufficient funds.")

    def test_transfer_funds_success(self):
        """Test a successful transfer of funds."""
        response = self.client.post(reverse('transfer_funds'), {'from_account': '123', 'to_account': '456', 'amount': '300'})
        
        self.assertEqual(response.status_code, 200)
        self.account1.refresh_from_db()
        self.account2.refresh_from_db()
        self.assertEqual(self.account1.balance, Decimal('700.00'))
        self.assertEqual(self.account2.balance, Decimal('800.00'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[-1]), "Successfully transferred 300 from Alice to Bob.")

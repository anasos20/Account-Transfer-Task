from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib import messages

from io import TextIOWrapper
from decimal import Decimal
import csv

from .models import Account

def home(request):
    return render(request, 'base.html')

def import_accounts(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'This is not a csv file')
            return redirect('import_accounts')
        
        try:
            csv_data = TextIOWrapper(csv_file.file, encoding="utf-8")
            reader = csv.reader(csv_data)
            
            # Validate header row
            header = next(reader, None)
            expected_headers = ['ID', 'Name', 'Balance']
            if header != expected_headers:
                messages.error(request, f"Invalid CSV format. Expected headers: {', '.join(expected_headers)}.")
                return redirect("import_accounts")
            
            accounts_processed = 0
            duplicate_account_numbers = set()
            
            for line_number, row in enumerate(reader, start=2):
                if len(row) != 3:
                    messages.error(request, f"Invalid data on line {line_number}: {row}. Expected 3 columns.")
                    continue

                account_number, account_name, balance = row
                
                # Validate account_number
                if not account_number:
                    messages.error(request, f"Missing account number on line {line_number}.")
                    continue
                
                if account_number in duplicate_account_numbers:
                    messages.error(request, f"Duplicate account number in CSV file: '{account_number}' (line {line_number}).")
                    continue
                
                duplicate_account_numbers.add(account_number)

                # Validate account_name
                if not account_name:
                    messages.error(request, f"Missing account name on line {line_number}.")
                    continue

                # Create or update the Account record
                Account.objects.update_or_create(
                    account_number=account_number,
                    defaults={
                        'account_name': account_name,
                        'balance': balance,
                    },
                )
                accounts_processed += 1
            
            if accounts_processed > 0:
                messages.success(request, f"Successfully processed {accounts_processed} accounts.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    return render(request, "account_transfer/import_csv.html")


def list_all_accounts(request):
    accounts = Account.objects.all()
    return render(request, 'account_transfer/list_accounts.html', {'accounts': accounts})

def get_account_info(request, account_number):
    account = Account.objects.get(account_number=account_number)
    return render(request, 'account_transfer/account_info.html', {'account': account})

@transaction.atomic
def transfer_funds(request):
    if request.method == 'POST':
        from_account_number = request.POST.get('from_account')
        to_account_number = request.POST.get('to_account')
        amount = Decimal(request.POST.get('amount'))
        
        try:
            from_account = Account.objects.select_for_update().get(account_number=from_account_number)
            to_account = Account.objects.select_for_update().get(account_number=to_account_number)
            
            amount = amount
            if amount <= 0:
                messages.error(request, "Amount must be greater than zero.")
            elif from_account.balance < amount:
                messages.error(request, "Insufficient funds.")
            else:
                from_account.balance -= amount
                to_account.balance += amount
                from_account.save()
                to_account.save()
                messages.success(request, f"Successfully transferred {amount} from {from_account.account_name} to {to_account.account_name}.")
        except Account.DoesNotExist:
            messages.error(request, "Invalid account number.")
        except ValueError:
            messages.error(request, "Invalid amount.")

    accounts = Account.objects.all()
    return render(request, 'account_transfer/transfer_funds.html', {'accounts': accounts})
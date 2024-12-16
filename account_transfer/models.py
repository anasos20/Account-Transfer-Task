from django.db import models

class Account(models.Model):
    account_number = models.CharField(max_length=100)
    account_name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.account_name
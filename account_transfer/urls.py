from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('import/', views.import_accounts, name='import_accounts'),
    path('accounts/', views.list_all_accounts, name='list_accounts'),
    path('accounts/<str:account_number>/', views.get_account_info, name='account_detail'),
    path('transfer/', views.transfer_funds, name='transfer_funds'),
]
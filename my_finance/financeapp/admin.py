from django.contrib import admin
from .models import Category, Account, Balance

# Register your models here.
admin.site.register(Account)
admin.site.register(Balance)
admin.site.register(Category)

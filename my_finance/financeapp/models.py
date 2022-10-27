from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=50, null=False)
    dr_cr = models.BooleanField(null=False)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user_id', 'name'], name='class of username')
        ]

    def __str__(self):
        return f'{"dr" if self.dr_cr else "cr"}:  {self.name}'


class Balance(models.Model):
    sum = models.DecimalField(decimal_places=2, max_digits=15)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    performed = models.DateTimeField(auto_now_add=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.performed} -- {self.category}: {self.sum}'


class Account(models.Model):
    sum = models.DecimalField(decimal_places=2, max_digits=15)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.sum}'

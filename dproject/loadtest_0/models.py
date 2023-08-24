from django.db import models
from django_tenants.models import TenantMixin

class AggAuthor(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class AggBook(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(AggAuthor, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title


class ModelA(models.Model):
    field_a1 = models.CharField(max_length=50)
    field_a2 = models.IntegerField()
    field_a3 = models.BooleanField()
    field_a4 = models.DateField()
    field_a5 = models.DecimalField(max_digits=10, decimal_places=2)
    field_a6 = models.TextField()
    field_a7 = models.EmailField()
    field_a8 = models.URLField()
    field_a9 = models.ImageField(upload_to='images/')
    field_a10 = models.FloatField()

class ModelB(models.Model):
    field_b1 = models.CharField(max_length=50)
    field_b2 = models.IntegerField()
    field_b3 = models.BooleanField()
    field_b4 = models.DateField()
    field_b5 = models.DecimalField(max_digits=10, decimal_places=2)
    field_b6 = models.TextField()
    field_b7 = models.EmailField()
    field_b8 = models.URLField()
    field_b9 = models.ImageField(upload_to='images/')
    field_b10 = models.FloatField()
    model_a = models.ForeignKey(ModelA, on_delete=models.CASCADE)

class ModelC(models.Model):
    field_c1 = models.CharField(max_length=50)
    field_c2 = models.IntegerField()
    field_c3 = models.BooleanField()
    field_c4 = models.DateField()
    field_c5 = models.DecimalField(max_digits=10, decimal_places=2)
    field_c6 = models.TextField()
    field_c7 = models.EmailField()
    field_c8 = models.URLField()
    field_c9 = models.ImageField(upload_to='images/')
    field_c10 = models.FloatField()
    model_b = models.OneToOneField(ModelB, on_delete=models.CASCADE)


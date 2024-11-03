from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

class Customer(models.Model):
    full_name = models.CharField(max_length=100)  # Name of the customer
    phone_number = models.CharField(max_length=15, unique=True, primary_key=True)  # Phone number (unique to avoid duplicates)
    number_of_pax = models.PositiveIntegerField(default=0)  # Number of people in the group
    
class Staff(models.Model):
    id = models.CharField(primary_key=True, unique=True, max_length=15)  # Staff ID as primary key
    staff_image = models.ImageField(upload_to='staff_images/', blank=True, null=True)  # Field for uploading images
    staff_name = models.CharField(max_length=100)  # Staff name
    staff_phone_number = models.CharField(max_length=15, unique=True)  # Unique phone number
    staff_email = models.EmailField(max_length=255, unique=True)  # Unique email address
    password = models.CharField(max_length=128)  # Password for storing hashed passwords
    role = models.CharField(max_length=10, default='Staff')  # Role field with default value 'Staff'
        
class Admin(models.Model):
    id = models.CharField(primary_key=True, unique=True, max_length=15)
    admin_name = models.CharField(max_length=100)
    admin_phone_number = models.CharField(max_length=15, unique=True)
    admin_email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=20, default='Admin')

class Menu(models.Model):
    menu_id = models.CharField(primary_key=True, max_length=20, unique=True)
    menu_name = models.CharField(max_length=100)
    menu_image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    menu_description = models.CharField(max_length=200)
    menu_price = models.DecimalField(max_digits=10, decimal_places=2)
    menu_availability = models.CharField(max_length=50)

class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    menu_items = models.JSONField(default=dict)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_ordered = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default='Pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True, default='Unpaid')
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    queue_number = models.IntegerField(null=True, blank=True)
    table_number = models.IntegerField(null=True, blank=True)
    is_verified = models.CharField(default='Pending', max_length=20)
    




    

from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer, Staff, Admin, Menu, Order
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal 
from django.http import JsonResponse
from .forms import ReceiptUploadForm
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.utils.timezone import now  # Ensure this import is present
from django.db.models import Min


# Customer login page view
def loginpage(request):
    if request.method == 'POST':
        # Capture form data
        cust_full_name = request.POST['full_name']
        cust_phone_number = request.POST['phone_number']
        cust_number_of_pax = request.POST['number_of_pax']

        # Check if the customer already exists
        customer, created = Customer.objects.get_or_create(
            phone_number=cust_phone_number,
            defaults={'full_name': cust_full_name, 'number_of_pax': cust_number_of_pax}
        )

        # Update details if the customer already exists
        if not created:
            customer.full_name = cust_full_name
            customer.number_of_pax = cust_number_of_pax
            customer.save()
        else:
            messages.success(request, "Customer saved successfully.")

        # Store customer's name in the session
        request.session['customer_phone'] = customer.phone_number
        request.session['customer_name'] = customer.full_name

        # Redirect to the menu page
        return redirect('menupagecust')

    return render(request, 'loginpage.html')

# Customer menu page view
def menupagecust(request):
    menu_items = Menu.objects.all()
    customer_name = request.session.get('customer_name', 'Guest')

    context = {
        'customer_name': customer_name,
        'menu_items': menu_items
    }

    return render(request, 'menupagecust.html', context)


from decimal import Decimal

def cartpage(request):
    # Retrieve customer phone number from the session
    customer_phone = request.session.get('customer_phone')
    if not customer_phone:
        return redirect('loginpage')

    # Get the customer object
    customer = get_object_or_404(Customer, phone_number=customer_phone)
    
    # Get the customer's pending order
    order = Order.objects.filter(customer=customer, status='Pending').first()

    if order:
        # Extract the menu item IDs from the order
        menu_item_ids = order.menu_items.keys()
        menu_items = Menu.objects.filter(menu_id__in=menu_item_ids)

        # Prepare a list of items with their quantities and individual total prices
        order_item_details = []
        for menu_item in menu_items:
            # Fetch the quantity for the current menu item
            quantity = order.menu_items.get(str(menu_item.menu_id), 0)

            # Ensure menu_price is a Decimal
            menu_price = Decimal(menu_item.menu_price)

            # Calculate the total price for this item
            total_price = menu_price * Decimal(quantity)

            order_item_details.append({
                'item': menu_item,  # Pass the entire menu item object for use in the template
                'quantity': quantity,
                'total_price': total_price
            })

        # Calculate the total price for the entire order
        total_price = sum(item['total_price'] for item in order_item_details)

        # Update the order's total_price field
        order.total_price = total_price
        order.save()  # Save the updated order total price if necessary

    else:
        # No pending order, set default values
        order_item_details = []
        total_price = Decimal(0)  # Use Decimal for consistency

    # Pass the items and total price to the template
    context = {
        'order_items': order_item_details,
        'total_price': total_price
    }

    return render(request, 'cartpage.html', context)


def add_to_cart(request, menu_id):
    # Check if the customer is logged in via session
    customer_phone = request.session.get('customer_phone')
    if not customer_phone:
        return redirect('loginpage')

    # Retrieve the customer and menu item or raise 404 if not found
    customer = get_object_or_404(Customer, phone_number=customer_phone)
    menu_item = get_object_or_404(Menu, menu_id=menu_id)
    
    # Retrieve or create an order with status 'Pending'
    order, created = Order.objects.get_or_create(customer=customer, status='Pending')

    # Ensure that order.menu_items is a dictionary
    if order.menu_items is None:
        order.menu_items = {}

    # Convert the menu_id to string to store it as a key
    menu_id_str = str(menu_id)

    # Add or update the item quantity in the cart
    if menu_id_str in order.menu_items:
        # Update the quantity of the existing item
        order.menu_items[menu_id_str] += 1
    else:
        # Add a new item to the cart with quantity 1
        order.menu_items[menu_id_str] = 1

    # Save the order with updated cart (no need to update total_price here)
    order.save()

    return redirect('menupagecust')  # Redirect to the cart page to see updated items





def increase_quantity(request, menu_id):
    customer_phone = request.session.get('customer_phone')
    customer = get_object_or_404(Customer, phone_number=customer_phone)
    order = Order.objects.filter(customer=customer, status='Pending').first()

    if order:
        # Get current menu item
        menu_item = get_object_or_404(Menu, menu_id=menu_id)
        order.menu_items[str(menu_id)] += 1
        order.save()

    return redirect('cartpage')


def decrease_quantity(request, menu_id):
    customer_phone = request.session.get('customer_phone')
    customer = get_object_or_404(Customer, phone_number=customer_phone)
    order = Order.objects.filter(customer=customer, status='Pending').first()

    if order:
        # Get current menu item
        menu_item = get_object_or_404(Menu, menu_id=menu_id)
        if order.menu_items[str(menu_id)] > 1:
            order.menu_items[str(menu_id)] -= 1
        else:
            del order.menu_items[str(menu_id)]  # Remove item if quantity is zero
        order.save()

    return redirect('cartpage')




def payment(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        receipt = request.FILES.get('receipt')

        if not receipt or not payment_method:
            return JsonResponse({'error': 'Both payment method and receipt are required.'}, status=400)

        customer_phone = request.session.get('customer_phone')
        if not customer_phone:
            return JsonResponse({'error': 'Customer not found in session.'}, status=400)

        customer = get_object_or_404(Customer, phone_number=customer_phone)
        order = get_object_or_404(Order, customer=customer, status='Pending')

        # File validation
        if not receipt.name.endswith(('.png', '.jpg', '.jpeg')):
            return JsonResponse({'error': 'Invalid file type. Only .png, .jpg, and .jpeg are allowed.'}, status=400)

        fs = FileSystemStorage()
        filename = fs.save(receipt.name, receipt)
        order.receipt = filename
        order.payment_method = payment_method

        # Assign queue number
        if order.status == 'Pending':
            order.status = 'Paid'
            last_order = Order.objects.filter(queue_number__isnull=False).order_by('-queue_number').first()
            order.queue_number = (last_order.queue_number + 1) if last_order else 1

        order.save()
        return JsonResponse({'success': 'Payment processed successfully!'})

    customer_phone = request.session.get('customer_phone')
    if customer_phone:
        customer = get_object_or_404(Customer, phone_number=customer_phone)
        order = get_object_or_404(Order, customer=customer, status='Pending')
        
        total_price = order.total_price
        return render(request, 'payment.html', {'order': order, 'total_price': total_price})
    
    return redirect('payment')


def submittedorder(request):
    customer_phone = request.session.get('customer_phone')
    if not customer_phone:
        return redirect('loginpage')

    # Retrieve the customer based on their phone number
    customer = get_object_or_404(Customer, phone_number=customer_phone)

    # Retrieve orders for the specific customer, ordered by date_ordered descending
    orders = Order.objects.filter(customer=customer).order_by('-date_ordered')

    order_details = []
    smallest_unverified_queue_number = None  # Variable to hold the smallest unverified queue number

    if not orders:
        # Render a message if no orders are found
        return render(request, 'submittedorder.html', {
            'message': "You have no submitted orders.",
            'customer_phone': customer.phone_number  # Include phone number in context
        })

    for order in orders:
        ordered_items = []
        # Loop through the menu_items JSONField
        for menu_id, quantity in order.menu_items.items():
            print(f"Checking menu_id: {menu_id}")  # Debug output
            menu_item = Menu.objects.filter(menu_id=menu_id).first()
            
            if menu_item is not None:
                ordered_items.append({
                    'menu_name': menu_item.menu_name,
                    'menu_price': menu_item.menu_price,
                    'quantity': quantity,
                    'total_item_price': menu_item.menu_price * quantity,
                })
            else:
                print(f"Menu item with id {menu_id} not found.")  # Log or handle missing menu item


        order_summary = {
            'order_id': order.order_id,
            'date_ordered': order.date_ordered,
            'total_price': order.total_price,
            'status': order.status,
            'table_number': order.table_number,
            'queue_number': order.queue_number,
            'is_verified': order.is_verified,
            'ordered_items': ordered_items,  # Add the ordered items with details
            'customer_name': customer.full_name,  # Include the customer's full name
            'customer_phone': customer.phone_number  # Include the customer's phone number
        }
        
        order_details.append(order_summary)

        # Check if the order is unverified and has a queue number
        if order.queue_number is not None and order.is_verified == 'Pending':
            if smallest_unverified_queue_number is None or order.queue_number < smallest_unverified_queue_number:
                smallest_unverified_queue_number = order.queue_number

    return render(request, 'submittedorder.html', {
        'orders': order_details,
        'smallest_unverified_queue_number': smallest_unverified_queue_number,
        'customer_phone': customer.phone_number  # Include phone number in context
    })


def complete_order(request):
    customer_phone = request.session.get('customer_phone')
    if not customer_phone:
        return redirect('loginpage')

    customer = get_object_or_404(Customer, phone_number=customer_phone)
    order = Order.objects.filter(customer=customer, status='Pending').first()

    if order:
        # Mark the order as completed in the `Order` table
        order.status = 'Completed'
        order.save()

        # Save a copy of the completed order to the `OrderHistory` table
        Order.objects.create(
            order=order,
            customer=order.customer,
            date_completed=timezone.now(),
            total_price=order.total_price,
            payment_method=order.payment_method,
            status='Completed'
        )

        # Optionally, return a success message
        messages.success(request, 'Order completed successfully!')

    return redirect('cartpage')


def staffadminlogin(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')
        user_role = request.POST.get('role')

        # Clear previous messages for a new login attempt
        messages.get_messages(request)

        if user_role == 'Staff':
            try:
                staff = Staff.objects.get(id=user_id)
                if staff.password == password:
                    request.session['staff_name'] = staff.staff_name
                    request.session['role'] = 'Staff'
                    return redirect('staffdashboard')
                else:
                    messages.error(request, "Invalid password for Staff.")
            except Staff.DoesNotExist:
                messages.error(request, "Staff not found.")

        elif user_role == 'Admin':
            try:
                admin = Admin.objects.get(id=user_id)
                if admin.password == password:
                    request.session['admin_name'] = admin.admin_name
                    request.session['role'] = 'Admin'
                    return redirect('admindashboard')
                else:
                    messages.error(request, "Invalid password for Admin.")
            except Admin.DoesNotExist:
                messages.error(request, "Admin not found.")

    # Render the login template with messages included
    return render(request, 'staffadminlogin.html', {'error': messages.get_messages(request)})


def admindashboard(request):
    # Check if the user is an admin
    if request.session.get('role') == 'Admin':
        admin_name = request.session.get('admin_name', 'Admin')

        # Get totals for menus, users, and reports
        total_menus = Menu.objects.count()  # Total number of menu items
        total_users = Staff.objects.count()  # Total number of users

        # Pass data to the template
        context = {
            'admin_name': admin_name,
            'total_menus': total_menus,
            'total_users': total_users,
        }

        return render(request, 'admindashboard.html', context)
    else:
        return redirect('staffadminlogin')

def useradmin(request):
    staff_members = Staff.objects.all()
    return render(request, 'useradmin.html', {'staff_members': staff_members})

def add_user(request):
    if request.method == 'POST':
        staff_id = request.POST['staff_id']
        staff_name = request.POST['staff_name']
        staff_email = request.POST['staff_email']
        staff_phone_number = request.POST['staff_phone_number']
        password = request.POST['password']
        role = request.POST['role']
        staff_image = request.FILES.get('staff_image')

        staff = Staff(
            id=staff_id,
            staff_name=staff_name,
            staff_email=staff_email,
            staff_phone_number=staff_phone_number,
            password=password,  # Hashing should be implemented
            role=role,
            staff_image=staff_image
        )
        staff.save()
        messages.success(request, 'User added successfully!')
        return redirect('useradmin')

    return render(request, 'useradmin.html')

def menuadmin(request):
    if request.method == 'POST':
        menu_id = request.POST['menu_id']
        menu_name = request.POST['menu_name']
        menu_description = request.POST['menu_description']
        menu_price = request.POST['menu_price']
        menu_availability = request.POST['menu_availability']
        menu_image = request.FILES.get('menu_image')

        menu_item = Menu(
            menu_id=menu_id,
            menu_name=menu_name,
            menu_description=menu_description,
            menu_price=menu_price,
            menu_availability=menu_availability,
            menu_image=menu_image
        )
        menu_item.save()

        messages.success(request, 'Menu item added successfully!')
        return redirect('menuadmin')

    menu_items = Menu.objects.all()
    return render(request, 'menuadmin.html', {'menu_items': menu_items})

def delete_menu(request, menu_id):
    if request.method == 'POST':
        menu_item = get_object_or_404(Menu, menu_id=menu_id)
        menu_item.delete()
        messages.success(request, 'Menu item deleted successfully!')
        return redirect('menuadmin')
    else:
        messages.error(request, 'Invalid request method.')
        return redirect('menuadmin')
    
def delete_user(request, staff_id):
    # Get the staff object based on the primary key 'id'
    staff = get_object_or_404(Staff, id=staff_id)  # Use 'id' if it's the primary key
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Staff member deleted successfully!')
        return redirect('useradmin')  # Redirect to your user admin page after deletion
    else:
        messages.error(request, 'Invalid request method.')
        return redirect('useradmin')


def report(request):
    # Get all orders from the database
    orders = Order.objects.all()

    # Prepare to store ordered items
    ordered_items = []

    for order in orders:
        items = []
        # Loop through the menu_items JSONField
        for menu_id, quantity in order.menu_items.items():
            # Fetch menu details
            try:
                menu_item = Menu.objects.get(menu_id=menu_id)
                items.append({
                    'menu_name': menu_item.menu_name,
                    'menu_price': menu_item.menu_price,
                    'quantity': quantity,
                    'total_item_price': menu_item.menu_price * quantity,
                })
            except Menu.DoesNotExist:
                # If the menu item does not exist, handle the exception
                items.append({
                    'menu_name': 'Unknown Menu Item',
                    'menu_price': 0,
                    'quantity': quantity,
                    'total_item_price': 0,
                })

        ordered_items.append((order, items))

    # Calculate total sales and other metrics
    total_orders = orders.count()
    total_sales = sum(order.total_price for order in orders)

    # Get paid and unpaid orders
    paid_orders = orders.filter(payment_method__isnull=False).filter(payment_method__in=['QR Code', 'Account Transfer'])
    total_paid_sales = sum(order.total_price for order in paid_orders)

    unpaid_orders = orders.filter(payment_method='Unpaid')
    total_unpaid_sales = sum(order.total_price for order in unpaid_orders)

    # Prepare context to pass to the template
    context = {
        'orders': orders,
        'ordered_items': ordered_items,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'paid_orders': paid_orders,
        'total_paid_sales': total_paid_sales,
        'unpaid_orders': unpaid_orders,
        'total_unpaid_sales': total_unpaid_sales,
        'report_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),  # Format the report date
    }

    return render(request, 'report.html', context)

def change_admin(request):
    if request.method == 'POST':
        # Old Admin ID
        old_admin_id = request.POST['old_admin_id']

        # Old admin details
        old_admin_name = request.POST['old_admin_name']
        old_admin_phone = request.POST['old_admin_phone']
        old_admin_email = request.POST['old_admin_email']
        old_admin_password = request.POST['old_admin_password']

        # New admin details
        new_admin_id = request.POST['new_admin_id']
        new_admin_name = request.POST['new_admin_name']
        new_admin_phone = request.POST['new_admin_phone']
        new_admin_email = request.POST['new_admin_email']
        new_admin_password = request.POST['new_admin_password']

        # Verify old admin information
        try:
            admin = Admin.objects.get(id=old_admin_id)

            if (admin.admin_name == old_admin_name and
                admin.admin_phone_number == old_admin_phone and
                admin.admin_email == old_admin_email and
                admin.password == old_admin_password):
                
                # Update admin details
                admin.id = new_admin_id
                admin.admin_name = new_admin_name
                admin.admin_phone_number = new_admin_phone
                admin.admin_email = new_admin_email
                admin.password = new_admin_password
                admin.save()

                messages.success(request, 'Admin details added successfully!')
                return redirect('useradmin')
            else:
                messages.error(request, 'Old admin details are incorrect. Please try again.')
                return redirect('useradmin')  # Redirecting instead of rendering

        except Admin.DoesNotExist:
            messages.error(request, 'Old Admin ID does not exist. Please try again.')
            return redirect('useradmin')  # Redirecting instead of rendering

    return render(request, 'useradmin.html')

def staffdashboard(request):
    total_orders = Order.objects.count()  # Get total number of orders

    # Create a context dictionary with total orders and pending orders
    context = {
        'total_orders': total_orders,
    }

    if request.session.get('role') == 'Staff':
        # Add staff name to the context
        staff_name = request.session.get('staff_name', 'Staff')
        context['staff_name'] = staff_name  # Add staff_name to the context
        return render(request, 'staffdashboard.html', context)  # Pass the full context
    else:
        return redirect('staffadminlogin')

    
def orderlist(request):
    # Get all orders, sorting first by verification status and then by queue number
    orders = Order.objects.all().order_by('is_verified', 'queue_number')  # Unverified orders first, then by queue number
    return render(request, 'orderlist.html', {'orders': orders})

# View to update the table number
def update_table_number(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_table_number = request.POST.get('table_number')
        
        try:
            order = Order.objects.get(order_id=order_id)
            order.table_number = new_table_number
            order.save()
            return redirect('orderlist')  # Redirect to the order list after updating
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found.'}, status=404)

# View to verify an order
def verify_order(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = Order.objects.get(order_id=order_id)
            order.is_verified = 'Verified'  # Set the verification status to 'Verified'
            order.save()
            return redirect('orderlist')  # Redirect to the order list page after verification
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found.'}, status=404)
    return redirect('orderlist')  # Redirect for any invalid request method

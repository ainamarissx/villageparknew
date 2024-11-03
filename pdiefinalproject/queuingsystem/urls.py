from django.urls import path
from . import views

urlpatterns = [
    path('', views.loginpage, name='loginpage'),  # Root login page
    path('loginpage/menupagecust/', views.menupagecust, name='menupagecust'),  # Customer menu page
    path('loginpage/cartpage/', views.cartpage, name='cartpage'),  # Cart page
    path('loginpage/add_to_cart/<int:menu_id>/', views.add_to_cart, name='add_to_cart'),  # Add to cart
    path('loginpage/payment/', views.payment, name='payment'),
    path('loginpage/payment/submittedorder/', views.submittedorder, name='submittedorder'),

    
    
    path('loginpage/increase_quantity/<int:menu_id>/', views.increase_quantity, name='increase_quantity'),  # Increase quantity
    path('loginpage/decrease_quantity/<int:menu_id>/', views.decrease_quantity, name='decrease_quantity'),  # Decrease quantity


    path('loginpage/staffadminlogin/', views.staffadminlogin, name='staffadminlogin'),  # Staff/Admin login
    path('loginpage/staffadminlogin/admindashboard/', views.admindashboard, name='admindashboard'),  # Admin dashboard
    path('loginpage/staffadminlogin/useradmin/', views.useradmin, name='useradmin'),  # User admin
    path('loginpage/staffadminlogin/add_user/', views.add_user, name='add_user'),  # Add user
    path('loginpage/staffadminlogin/menuadmin/', views.menuadmin, name='menuadmin'),  # Menu admin
    path('loginpage/staffadminlogin/menuadmin/delete/<str:menu_id>/', views.delete_menu, name='delete_menu'),  # Delete menu item
    path('loginpage/staffadminlogin/delete_user/<str:staff_id>/', views.delete_user, name='delete_user'),
    
    path('loginpage/staffadminlogin/menuadmin/report/', views.report, name='report'),  # Report page
    
    path('loginpage/staffadminlogin/change_admin/', views.change_admin, name='change_admin'),
    
    path('loginpage/staffadminlogin/staffdashboard/', views.staffdashboard, name='staffdashboard'),  
    path('loginpage/staffadminlogin/orderlist/', views.orderlist, name='orderlist'),
    path('loginpage/staffadminlogin/orderlist/update_table_number/', views.update_table_number, name='update_table_number'),  # URL for updating the table number
    path('loginpage/staffadminlogin/orderlist/verify_order/', views.verify_order, name='verify_order'),
]

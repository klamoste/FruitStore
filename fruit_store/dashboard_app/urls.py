from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin-tools/', views.admin_tool_page, name='admin_tool_page'),
    path('products-tools/', views.products_tool_page, name='products_tool_page'),
    path('users-tools/', views.users_tool_page, name='users_tool_page'),
    path('users-tools/create-customer/', views.create_customer_tool_page, name='create_customer_tool_page'),
    path('storefront-tools/', views.storefront_tool_page, name='storefront_tool_page'),
]

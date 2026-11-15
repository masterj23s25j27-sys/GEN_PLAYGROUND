from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('management_dashboard/', views.management_dashboard, name='management_dashboard'),
    path('management/delete/<str:emp_id>/', views.delete_employee, name='delete_employee'),
    path('management/reset/', views.reset_database, name='reset_database'),
    path('action/', views.action_punch, name='action_punch'),
    path('scan/<uuid:token>/', views.scan_qr, name='scan_qr'),
    path('management/update-status/<str:emp_id>/<str:action>/', views.manager_update_status, name='manager_update_status'),
]

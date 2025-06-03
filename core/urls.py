from django.contrib.auth import views as auth_views
from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home, name='home'),
    path('team/create/', views.team_create, name='team_create'),
    path('team/join/', views.team_join, name='team_join'),
    path('team/<int:team_id>/', views.team_detail, name='team_detail'),
    path('team/<int:team_id>/edit/', views.team_edit, name='team_edit'),
    path('team/<int:team_id>/leave/', views.team_leave, name='team_leave'),
    path('team/<int:team_id>/delete/', views.team_delete, name='team_delete'),
    path('team/<int:team_id>/member/<int:membership_id>/remove/', views.team_remove_member, name='team_remove_member'),
    path('team/<int:team_id>/member/<int:membership_id>/change_role/', views.team_change_role, name='team_change_role'),
    
    # Stand-up management
    path('standup/new/', views.standup_create, name='standup_create'),
    path('standup/<int:entry_id>/edit/', views.standup_edit, name='standup_edit'),
    path('standup/<int:entry_id>/delete/', views.standup_delete, name='standup_delete'),
    path('standup/history/', views.standup_list, name='standup_list'),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
]
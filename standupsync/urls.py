from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('team/create/', views.team_create, name='team_create'),
    path('team/join/', views.team_join, name='team_join'),
    path('team/<int:team_id>/', views.team_detail, name='team_detail'),
    path('team/<int:team_id>/edit/', views.team_edit, name='team_edit'),
    path('team/<int:team_id>/leave/', views.team_leave, name='team_leave'),
    path('team/<int:team_id>/delete/', views.team_delete, name='team_delete'),
    path('team/<int:team_id>/change-role/<int:membership_id>/', views.team_change_role, name='team_change_role'),
    path('team/<int:team_id>/remove-member/<int:membership_id>/', views.team_remove_member, name='team_remove_member'),
    path('standup/', views.standup_list, name='standup_list'),
    path('standup/create/', views.standup_create, name='standup_create'),
    path('standup/<int:entry_id>/edit/', views.standup_edit, name='standup_edit'),
    path('standup/<int:entry_id>/delete/', views.standup_delete, name='standup_delete'),
] 
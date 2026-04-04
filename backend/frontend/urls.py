from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('candidate/<int:pk>/', views.candidate_detail, name='frontend-candidate-detail'),
    path('panel/', views.panel_view, name='panel'),
    path('panel/login/', views.panel_login, name='panel-login'),
    path('panel/login-page/', views.panel_login_page, name='panel-login-page'),
    path('panel/logout/', views.panel_logout, name='panel-logout'),
    path('teacher/', views.teacher_view, name='teacher-panel'),
    path('teacher/logout/', views.teacher_logout, name='teacher-logout'),
]

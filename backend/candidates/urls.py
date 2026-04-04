from django.urls import path
from . import views
urlpatterns = [
    path('applications/', views.application_list_create, name='application-list-create'),
    path('applications/<int:pk>/', views.application_detail, name='application-detail'),
    path('cities/', views.city_list, name='city-list'),
    path('cities/<str:city>/regions/', views.city_regions, name='city-regions'),
    path('admin/login/', views.admin_login, name='admin-api-login'),
    path('admin/applications/', views.admin_applications, name='admin-applications'),
    path('admin/applications/score-all/', views.admin_score_all_applications, name='admin-score-all-applications'),
    path('admin/applications/<int:pk>/score/', views.admin_score_application, name='admin-score-application'),
    path('teacher/nominations/', views.teacher_nominations, name='teacher-nominations'),
    path('admin/nominations/', views.admin_nominations_list, name='admin-nominations-list'),
    path('admin/nominations/<int:pk>/review/', views.admin_nomination_review, name='admin-nomination-review'),
    path('candidates/', views.candidate_list_create, name='candidate-list-create'),
    path('candidates/search/', views.candidate_search, name='candidate-search'),
    path('candidates/ranking/', views.candidate_ranking, name='candidate-ranking'),
    path('candidates/score-all/', views.score_all, name='score-all'),
    path('candidates/<int:pk>/', views.candidate_detail, name='candidate-detail'),
    path('candidates/<int:pk>/score/', views.candidate_score, name='candidate-score'),
]

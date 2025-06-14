from django.urls import path
from . import views
from . import consumers

urlpatterns = [
    # Admin/Teacher URLs
    path('', views.index, name='index'),
    path('signup/', views.teacher_signup, name='signup'),
    path('login/', views.teacher_login, name='login'),
    #path('login/', views.teacher_login, name='teacher_login'),
    path('logout/', views.teacher_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/<uuid:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<uuid:session_id>/live/', views.live_monitoring, name='live_monitoring'),
    path('sessions/<uuid:session_id>/end/', views.end_session, name='end_session'),
    path('sessions/<uuid:session_id>/export/', views.export_session, name='export_session'),
    
    # Student URLs
    path('session/<uuid:session_id>/', views.student_login, name='student_login'),
    path('session/<uuid:session_id>/join/', views.student_join, name='student_join'),
    path('session/<uuid:session_id>/upload-profile/', views.upload_profile, name='upload_profile'),
    path('session/<uuid:session_id>/view-screen/', views.view_teacher_screen, name='view_teacher_screen'),
    
    # Detection URLs
    path('detection/face/', views.face_detection, name='face_detection'),
    path('detection/hand/', views.hand_detection, name='hand_detection'),
    
    # API URLs
    path('api/sessions/<uuid:session_id>/students/', views.api_session_students, name='api_session_students'),
    path('api/sessions/<uuid:session_id>/attendance/', views.api_session_attendance, name='api_session_attendance'),
    path('api/sessions/<uuid:session_id>/face-captures/', views.api_face_captures, name='api_face_captures'),
    path('api/attendance/override/', views.api_attendance_override, name='api_attendance_override'),
]

# WebSocket URL patterns will be defined in routing.py

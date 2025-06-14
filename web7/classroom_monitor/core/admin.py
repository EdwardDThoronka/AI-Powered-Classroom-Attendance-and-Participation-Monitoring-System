from django.contrib import admin
from .models import Teacher, Session, Student, SessionStudent, Attendance, Participation

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active', 'teacher')
    search_fields = ('name',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_id')
    search_fields = ('name', 'student_id')

@admin.register(SessionStudent)
class SessionStudentAdmin(admin.ModelAdmin):
    list_display = ('session', 'student', 'join_time')
    list_filter = ('session',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('session', 'student', 'is_present', 'manually_overridden', 'timestamp')
    list_filter = ('is_present', 'manually_overridden', 'session')

@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('attendance', 'event_type', 'timestamp')
    list_filter = ('event_type',)

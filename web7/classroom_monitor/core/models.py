from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser

class Teacher(AbstractUser):
    """Extended user model for teachers"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Session(models.Model):
    """Model for classroom sessions"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='sessions')
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    session_link = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

class Student(models.Model):
    """Model for students"""
    name = models.CharField(max_length=255)
    student_id = models.CharField(max_length=100, unique=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.student_id})"

class SessionStudent(models.Model):
    """Model for students joined in a session"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='session_students')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='session_students')
    join_time = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('session', 'student')
    
    def __str__(self):
        return f"{self.student.name} in {self.session.name}"

class Attendance(models.Model):
    """Model for attendance records"""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_present = models.BooleanField(default=True)
    manually_overridden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('session', 'student')
    
    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.name} - {status} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class Participation(models.Model):
    """Model for participation events (hand raises)"""
    EVENT_TYPES = (
        ('hand_raise', 'Hand Raise'),
        ('other', 'Other'),
    )
    
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='participations')
    timestamp = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, default='hand_raise')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.attendance.student.name} - {self.get_event_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class FaceCapture(models.Model):
    """Model for storing face capture images"""
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='face_captures')
    image = models.ImageField(upload_to='face_captures/')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Face capture for {self.attendance.student.name} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

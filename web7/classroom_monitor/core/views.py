from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import json
import csv
import os
import cv2
import numpy as np
import mediapipe as mp
import base64
from datetime import datetime
from .models import Teacher, Session, Student, SessionStudent, Attendance, Participation, FaceCapture
import uuid
import io
from PIL import Image
from django.core.files.base import ContentFile

# MediaPipe initialization
mp_face_detection = mp.solutions.face_detection
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Home page
def index(request):
    return render(request, 'core/index.html')

# Teacher authentication views
def teacher_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Validate input
        if not all([username, email, password, confirm_password, first_name, last_name]):
            return render(request, 'core/signup.html', {'error': 'All fields are required'})
        
        if password != confirm_password:
            return render(request, 'core/signup.html', {'error': 'Passwords do not match'})
        
        # Check if username or email already exists
        if Teacher.objects.filter(username=username).exists():
            return render(request, 'core/signup.html', {'error': 'Username already exists'})
        
        if Teacher.objects.filter(email=email).exists():
            return render(request, 'core/signup.html', {'error': 'Email already exists'})
        
        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            return render(request, 'core/signup.html', {'error': ' '.join(e.messages)})
        
        # Create new teacher account
        try:
            teacher = Teacher.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Log in the new user
            login(request, teacher)
            return redirect('dashboard')
        except Exception as e:
            return render(request, 'core/signup.html', {'error': f'Error creating account: {str(e)}'})
    
    return render(request, 'core/signup.html')

def teacher_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    return render(request, 'core/login.html')

@login_required
def teacher_logout(request):
    logout(request)
    return redirect('index')

# Dashboard and session management
@login_required
def dashboard(request):
    active_sessions = Session.objects.filter(teacher=request.user, is_active=True)
    recent_sessions = Session.objects.filter(teacher=request.user, is_active=False).order_by('-end_time')[:5]
    context = {
        'active_sessions': active_sessions,
        'recent_sessions': recent_sessions
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def session_list(request):
    sessions = Session.objects.filter(teacher=request.user).order_by('-start_time')
    context = {
        'sessions': sessions
    }
    return render(request, 'core/session_list.html', context)

@login_required
def create_session(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            session = Session.objects.create(
                teacher=request.user,
                name=name
            )
            return redirect('session_detail', session_id=session.session_link)
        else:
            return render(request, 'core/create_session.html', {'error': 'Session name is required'})
    return render(request, 'core/create_session.html')

@login_required
def session_detail(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, teacher=request.user)
    students = SessionStudent.objects.filter(session=session).select_related('student')
    attendances = Attendance.objects.filter(session=session).select_related('student')
    
    # Get participation counts
    participation_counts = {}
    face_captures = {}
    
    for attendance in attendances:
        # Get participation count
        participation_counts[attendance.student.id] = Participation.objects.filter(attendance=attendance).count()
        
        # Get latest face capture
        latest_face = FaceCapture.objects.filter(attendance=attendance).order_by('-timestamp').first()
        if latest_face:
            face_captures[attendance.student.id] = latest_face.image.url
    
    context = {
        'session': session,
        'students': students,
        'attendances': attendances,
        'participation_counts': participation_counts,
        'face_captures': face_captures,
        'session_url': request.build_absolute_uri(f'/session/{session.session_link}/')
    }
    return render(request, 'core/session_detail.html', context)

@login_required
def live_monitoring(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, teacher=request.user)
    students = SessionStudent.objects.filter(session=session).select_related('student')
    
    context = {
        'session': session,
        'students': students,
    }
    return render(request, 'core/live_monitoring.html', context)

@login_required
def end_session(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, teacher=request.user)
    if session.is_active:
        session.is_active = False
        session.end_time = timezone.now()
        session.save()
    return redirect('session_detail', session_id=session.session_link)

@login_required
def export_session(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, teacher=request.user)
    attendances = Attendance.objects.filter(session=session).select_related('student')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="session_{session.name}_{session.start_time.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Student ID', 'Status', 'Join Time', 'Hand Raises'])
    
    for attendance in attendances:
        student = attendance.student
        session_student = SessionStudent.objects.filter(session=session, student=student).first()
        join_time = session_student.join_time if session_student else 'N/A'
        status = 'Present' if attendance.is_present else 'Absent'
        hand_raises = Participation.objects.filter(attendance=attendance).count()
        
        writer.writerow([
            student.name,
            student.student_id,
            status,
            join_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(join_time, datetime) else join_time,
            hand_raises
        ])
    
    return response

# Student views
def student_login(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, is_active=True)
    context = {
        'session': session
    }
    return render(request, 'core/student_login.html', context)

def student_join(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        student_id = request.POST.get('student_id')
        
        if not name or not student_id:
            return render(request, 'core/student_login.html', {
                'session': session,
                'error': 'Both name and student ID are required'
            })
        
        # Get or create student
        student, created = Student.objects.get_or_create(
            student_id=student_id,
            defaults={'name': name}
        )
        
        if not created and student.name != name:
            student.name = name
            student.save()
        
        # Add student to session
        session_student, created = SessionStudent.objects.get_or_create(
            session=session,
            student=student
        )
        
        # Create attendance record
        attendance, created = Attendance.objects.get_or_create(
            session=session,
            student=student,
            defaults={'is_present': False}  # Will be updated when face is detected
        )
        
        context = {
            'session': session,
            'student': student,
            'joined': True
        }
        return render(request, 'core/student_joined.html', context)
    
    return redirect('student_login', session_id=session_id)

def view_teacher_screen(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, is_active=True)
    student_id = request.GET.get('student_id')
    
    if not student_id:
        return redirect('student_login', session_id=session_id)
    
    student = get_object_or_404(Student, student_id=student_id)
    
    context = {
        'session': session,
        'student': student
    }
    return render(request, 'core/view_teacher_screen.html', context)

def upload_profile(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, is_active=True)
    
    if request.method == 'POST' and request.FILES.get('profile_pic'):
        student_id = request.POST.get('student_id')
        if not student_id:
            return JsonResponse({'error': 'Student ID is required'}, status=400)
        
        student = get_object_or_404(Student, student_id=student_id)
        student.profile_pic = request.FILES['profile_pic']
        student.save()
        
        return JsonResponse({'success': True, 'message': 'Profile picture uploaded successfully'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Detection views
@csrf_exempt
def face_detection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            student_id = data.get('student_id')
            image_data = data.get('image_data')
            
            if not session_id or not student_id or not image_data:
                return JsonResponse({'error': 'Missing required data'}, status=400)
            
            # Get session and student
            session = get_object_or_404(Session, session_link=uuid.UUID(session_id), is_active=True)
            student = get_object_or_404(Student, student_id=student_id)
            
            # Process image for face detection
            image_data = image_data.split(',')[1]  # Remove data URL prefix
            image_bytes = base64.b64decode(image_data)
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # Detect faces
            with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:
                # Convert the BGR image to RGB
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = face_detection.process(img_rgb)
                
                if results.detections:
                    # Face detected, update attendance
                    attendance, created = Attendance.objects.get_or_create(
                        session=session,
                        student=student,
                        defaults={'is_present': True}
                    )
                    
                    if not attendance.is_present:
                        attendance.is_present = True
                        attendance.save()
                    
                    # Save face capture
                    # Convert the image to PIL format
                    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                    
                    # Save the image to a buffer
                    buffer = io.BytesIO()
                    pil_img.save(buffer, format='JPEG')
                    buffer.seek(0)
                    
                    # Create a ContentFile from the buffer
                    image_file = ContentFile(buffer.read(), name=f"{student.student_id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.jpg")
                    
                    # Create FaceCapture record
                    face_capture = FaceCapture.objects.create(
                        attendance=attendance,
                        image=image_file
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'face_detected': True,
                        'attendance_recorded': True,
                        'face_capture_url': face_capture.image.url
                    })
                else:
                    return JsonResponse({
                        'success': True,
                        'face_detected': False,
                        'attendance_recorded': False
                    })
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def hand_detection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            student_id = data.get('student_id')
            image_data = data.get('image_data')
            
            if not session_id or not student_id or not image_data:
                return JsonResponse({'error': 'Missing required data'}, status=400)
            
            # Get session and student
            session = get_object_or_404(Session, session_link=uuid.UUID(session_id), is_active=True)
            student = get_object_or_404(Student, student_id=student_id)
            
            # Get attendance record
            attendance = get_object_or_404(Attendance, session=session, student=student)
            
            # Process image for hand detection
            image_data = image_data.split(',')[1]  # Remove data URL prefix
            image_bytes = base64.b64decode(image_data)
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # Detect hands
            with mp_hands.Hands(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5) as hands:
                # Convert the BGR image to RGB
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = hands.process(img_rgb)
                
                hand_raised = False
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Check if hand is raised (wrist below index finger)
                        wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        
                        if wrist.y > index_finger_tip.y:
                            hand_raised = True
                            break
                
                if hand_raised:
                    # Record participation
                    participation = Participation.objects.create(
                        attendance=attendance,
                        event_type='hand_raise'
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'hand_detected': True,
                        'hand_raised': True,
                        'participation_recorded': True
                    })
                else:
                    return JsonResponse({
                        'success': True,
                        'hand_detected': bool(results.multi_hand_landmarks),
                        'hand_raised': False,
                        'participation_recorded': False
                    })
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# API views
@login_required
def api_session_students(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, teacher=request.user)
    students = SessionStudent.objects.filter(session=session).select_related('student')
    
    data = []
    for session_student in students:
        student = session_student.student
        attendance = Attendance.objects.filter(session=session, student=student).first()
        participation_count = Participation.objects.filter(attendance=attendance).count() if attendance else 0
        
        # Get latest face capture
        latest_face = None
        if attendance:
            latest_face = FaceCapture.objects.filter(attendance=attendance).order_by('-timestamp').first()
        
        data.append({
            'id': student.id,
            'name': student.name,
            'student_id': student.student_id,
            'join_time': session_student.join_time.isoformat(),
            'is_present': attendance.is_present if attendance else False,
            'participation_count': participation_count,
            'profile_pic': student.profile_pic.url if student.profile_pic else None,
            'face_capture': latest_face.image.url if latest_face else None
        })
    
    return JsonResponse({'students': data})

@login_required
def api_session_attendance(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, teacher=request.user)
    attendances = Attendance.objects.filter(session=session).select_related('student')
    
    data = []
    for attendance in attendances:
        student = attendance.student
        participation_count = Participation.objects.filter(attendance=attendance).count()
        
        # Get latest face capture
        latest_face = FaceCapture.objects.filter(attendance=attendance).order_by('-timestamp').first()
        
        data.append({
            'id': attendance.id,
            'student_name': student.name,
            'student_id': student.student_id,
            'is_present': attendance.is_present,
            'manually_overridden': attendance.manually_overridden,
            'timestamp': attendance.timestamp.isoformat(),
            'participation_count': participation_count,
            'face_capture': latest_face.image.url if latest_face else None
        })
    
    return JsonResponse({'attendances': data})

@login_required
def api_face_captures(request, session_id):
    session = get_object_or_404(Session, session_link=session_id, teacher=request.user)
    attendances = Attendance.objects.filter(session=session).select_related('student')
    
    data = {}
    for attendance in attendances:
        student_id = attendance.student.id
        latest_face = FaceCapture.objects.filter(attendance=attendance).order_by('-timestamp').first()
        if latest_face:
            data[student_id] = {
                'url': latest_face.image.url,
                'timestamp': latest_face.timestamp.isoformat()
            }
    
    return JsonResponse({'face_captures': data})

@login_required
@csrf_exempt
def api_attendance_override(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            attendance_id = data.get('attendance_id')
            is_present = data.get('is_present')
            
            if attendance_id is None or is_present is None:
                return JsonResponse({'error': 'Missing required data'}, status=400)
            
            attendance = get_object_or_404(Attendance, id=attendance_id)
            
            # Verify teacher owns the session
            if attendance.session.teacher != request.user:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
            
            attendance.is_present = is_present
            attendance.manually_overridden = True
            attendance.save()
            
            return JsonResponse({
                'success': True,
                'attendance': {
                    'id': attendance.id,
                    'student_name': attendance.student.name,
                    'student_id': attendance.student.student_id,
                    'is_present': attendance.is_present,
                    'manually_overridden': attendance.manually_overridden
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

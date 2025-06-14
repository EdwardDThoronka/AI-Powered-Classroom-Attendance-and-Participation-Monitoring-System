import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.shortcuts import get_object_or_404
from .models import Session, Student, Attendance, Participation, FaceCapture

class ScreenSharingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'screen_sharing_{self.session_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        # Handle different message types
        if message_type == 'start_sharing':
            await self.handle_start_sharing(data)
        elif message_type == 'stop_sharing':
            await self.handle_stop_sharing(data)
        elif message_type == 'offer':
            await self.handle_offer(data)
        elif message_type == 'answer':
            await self.handle_answer(data)
        elif message_type == 'candidate':
            await self.handle_candidate(data)
        elif message_type == 'student_connected':
            await self.handle_student_connected(data)
        elif message_type == 'student_disconnected':
            await self.handle_student_disconnected(data)
    
    # Handle start sharing message
    async def handle_start_sharing(self, data):
        session_id = data.get('session_id')
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'sharing_started',
                'session_id': session_id
            }
        )
    
    # Handle stop sharing message
    async def handle_stop_sharing(self, data):
        session_id = data.get('session_id')
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'sharing_stopped',
                'session_id': session_id
            }
        )
    
    # Handle offer message
    async def handle_offer(self, data):
        session_id = data.get('session_id')
        offer = data.get('offer')
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'offer_received',
                'session_id': session_id,
                'offer': offer
            }
        )
    
    # Handle answer message
    async def handle_answer(self, data):
        session_id = data.get('session_id')
        student_id = data.get('student_id')
        answer = data.get('answer')
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'answer_received',
                'session_id': session_id,
                'student_id': student_id,
                'answer': answer
            }
        )
    
    # Handle candidate message
    async def handle_candidate(self, data):
        session_id = data.get('session_id')
        student_id = data.get('student_id', None)
        candidate = data.get('candidate')
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'candidate_received',
                'session_id': session_id,
                'student_id': student_id,
                'candidate': candidate
            }
        )
    
    # Handle student connected message
    async def handle_student_connected(self, data):
        session_id = data.get('session_id')
        student_id = data.get('student_id')
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'student_connected',
                'session_id': session_id,
                'student_id': student_id
            }
        )
    
    # Handle student disconnected message
    async def handle_student_disconnected(self, data):
        session_id = data.get('session_id')
        student_id = data.get('student_id')
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'student_disconnected',
                'session_id': session_id,
                'student_id': student_id
            }
        )
    
    # Receive message from room group
    async def sharing_started(self, event):
        session_id = event['session_id']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'start_sharing',
            'session_id': session_id
        }))
    
    # Receive message from room group
    async def sharing_stopped(self, event):
        session_id = event['session_id']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'stop_sharing',
            'session_id': session_id
        }))
    
    # Receive message from room group
    async def offer_received(self, event):
        session_id = event['session_id']
        offer = event['offer']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'offer',
            'session_id': session_id,
            'offer': offer
        }))
    
    # Receive message from room group
    async def answer_received(self, event):
        session_id = event['session_id']
        student_id = event['student_id']
        answer = event['answer']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'answer',
            'session_id': session_id,
            'student_id': student_id,
            'answer': answer
        }))
    
    # Receive message from room group
    async def candidate_received(self, event):
        session_id = event['session_id']
        student_id = event.get('student_id')
        candidate = event['candidate']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'candidate',
            'session_id': session_id,
            'student_id': student_id,
            'candidate': candidate
        }))
    
    # Receive message from room group
    async def student_connected(self, event):
        session_id = event['session_id']
        student_id = event['student_id']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'student_connected',
            'session_id': session_id,
            'student_id': student_id
        }))
    
    # Receive message from room group
    async def student_disconnected(self, event):
        session_id = event['session_id']
        student_id = event['student_id']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'student_disconnected',
            'session_id': session_id,
            'student_id': student_id
        }))
    
    # Receive message from room group
    async def face_update(self, event):
        student_id = event['student_id']
        face_url = event['face_url']
        timestamp = event['timestamp']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'face_update',
            'student_id': student_id,
            'face_url': face_url,
            'timestamp': timestamp
        }))
    
    # Receive message from room group
    async def participation_update(self, event):
        student_id = event['student_id']
        count = event['count']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'participation_update',
            'student_id': student_id,
            'count': count
        }))

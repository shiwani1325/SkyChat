import json
import os
import uuid
import base64
import asyncio
from cryptography.fernet import Fernet
from django.conf import settings
from django.db.models import Q
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime



# class GroupEmployeeChat(AsyncWebsocketConsumer):
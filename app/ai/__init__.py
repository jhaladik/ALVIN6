# app/ai/__init__.py
from flask import Blueprint

ai_bp = Blueprint('ai', __name__)

from app.ai import routes
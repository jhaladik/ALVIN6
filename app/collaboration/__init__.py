# app/collaboration/__init__.py
from flask import Blueprint

collaboration_bp = Blueprint('collaboration', __name__)

from app.collaboration import routes
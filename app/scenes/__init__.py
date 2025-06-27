# app/scenes/__init__.py
from flask import Blueprint

scenes_bp = Blueprint('scenes', __name__)

from app.scenes import routes
# app/billing/__init__.py
from flask import Blueprint

billing_bp = Blueprint('billing', __name__)

from app.billing import routes
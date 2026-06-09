from flask import Blueprint

tools_bp = Blueprint('tools', __name__, url_prefix='/tools')

from . import routes  # noqa

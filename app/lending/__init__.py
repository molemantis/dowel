from flask import Blueprint

lending_bp = Blueprint('lending', __name__, url_prefix='/lending')

from . import routes  # noqa

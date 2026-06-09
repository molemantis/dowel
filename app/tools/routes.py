import os
import uuid
from datetime import datetime

from flask import (render_template, redirect, url_for, flash, request,
                   current_app, jsonify)
from flask_login import login_required, current_user
from PIL import Image

from ..models import db, Tool, Category, Checkout, Reservation, User
from ..lookup.service import search_product, fetch_product_image
from . import tools_bp


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def save_image(file, user_id):
    """Save and resize uploaded image, return filename."""
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.jpg"
    user_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    filepath = os.path.join(user_dir, filename)

    img = Image.open(file)
    img = img.convert('RGB')
    img.thumbnail((800, 800), Image.LANCZOS)
    img.save(filepath, 'JPEG', quality=85)
    return f"{user_id}/{filename}"


@tools_bp.route('/')
@tools_bp.route('/inventory')
@login_required
def index():
    categories = Category.query.order_by(Category.name).all()
    tools = Tool.query.filter_by(owner_id=current_user.id).order_by(Tool.created_at.desc()).all()
    return render_template('tools/index.html', tools=tools, categories=categories)


@tools_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Tool name is required.', 'danger')
            return render_template('tools/add.html', categories=categories)

        category_id = request.form.get('category_id') or None
        image_filename = None

        # Handle image upload
        if 'image' in request.files and request.files['image'].filename:
            f = request.files['image']
            if allowed_file(f.filename):
                image_filename = save_image(f, current_user.id)
            else:
                flash('Invalid image format.', 'danger')
                return render_template('tools/add.html', categories=categories)

        # Handle image URL (download)
        image_url = request.form.get('image_url', '').strip()
        if not image_filename and image_url:
            image_filename = fetch_product_image(image_url, current_user.id)

        # Parse specs
        spec_keys = request.form.getlist('spec_key')
        spec_vals = request.form.getlist('spec_val')
        specs = {k: v for k, v in zip(spec_keys, spec_vals) if k.strip()}

        year = request.form.get('year_purchased')
        tool = Tool(
            owner_id=current_user.id,
            category_id=int(category_id) if category_id else None,
            name=name,
            brand=request.form.get('brand', '').strip() or None,
            model_number=request.form.get('model_number', '').strip() or None,
            serial_number=request.form.get('serial_number', '').strip() or None,
            year_purchased=int(year) if year else None,
            condition=request.form.get('condition', 'good'),
            description=request.form.get('description', '').strip() or None,
            specs=specs or None,
            image_filename=image_filename,
            retailer_url=request.form.get('retailer_url', '').strip() or None,
            source=request.form.get('source', 'uploaded'),
        )
        db.session.add(tool)
        db.session.commit()
        flash(f'Tool "{tool.name}" added!', 'success')
        return redirect(url_for('tools.detail', tool_id=tool.id))

    return render_template('tools/add.html', categories=categories)


@tools_bp.route('/<int:tool_id>')
@login_required
def detail(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    if tool.owner_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('tools.index'))
    checkouts = tool.checkouts.order_by(Checkout.checked_out_at.desc()).all()
    pending_reservations = tool.reservations.filter_by(status='pending').order_by(Reservation.created_at).all()
    return render_template('tools/detail.html', tool=tool, checkouts=checkouts,
                           pending_reservations=pending_reservations)


@tools_bp.route('/<int:tool_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    if tool.owner_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('tools.index'))
    categories = Category.query.order_by(Category.name).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Tool name is required.', 'danger')
            return render_template('tools/edit.html', tool=tool, categories=categories)

        tool.name = name
        tool.category_id = int(request.form.get('category_id')) if request.form.get('category_id') else None
        tool.brand = request.form.get('brand', '').strip() or None
        tool.model_number = request.form.get('model_number', '').strip() or None
        tool.serial_number = request.form.get('serial_number', '').strip() or None
        year = request.form.get('year_purchased')
        tool.year_purchased = int(year) if year else None
        tool.condition = request.form.get('condition', 'good')
        tool.description = request.form.get('description', '').strip() or None
        tool.retailer_url = request.form.get('retailer_url', '').strip() or None

        spec_keys = request.form.getlist('spec_key')
        spec_vals = request.form.getlist('spec_val')
        tool.specs = {k: v for k, v in zip(spec_keys, spec_vals) if k.strip()} or None

        if 'image' in request.files and request.files['image'].filename:
            f = request.files['image']
            if allowed_file(f.filename):
                tool.image_filename = save_image(f, current_user.id)

        db.session.commit()
        flash('Tool updated.', 'success')
        return redirect(url_for('tools.detail', tool_id=tool.id))

    return render_template('tools/edit.html', tool=tool, categories=categories)


@tools_bp.route('/<int:tool_id>/delete', methods=['POST'])
@login_required
def delete(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    if tool.owner_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('tools.index'))
    db.session.delete(tool)
    db.session.commit()
    flash('Tool deleted.', 'success')
    return redirect(url_for('tools.index'))


@tools_bp.route('/lookup')
@login_required
def lookup():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'error': 'No query provided'}), 400
    result = search_product(q)
    if result:
        return jsonify(result)
    return jsonify({'error': 'No results found'}), 404


@tools_bp.route('/share/<share_token>')
def public_inventory(share_token):
    owner = User.query.filter_by(share_token=share_token).first_or_404()
    tools = Tool.query.filter_by(owner_id=owner.id).order_by(Tool.created_at.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('public/inventory.html', owner=owner, tools=tools, categories=categories)


@tools_bp.route('/share/<share_token>/reserve/<int:tool_id>', methods=['POST'])
def public_reserve(share_token, tool_id):
    owner = User.query.filter_by(share_token=share_token).first_or_404()
    tool = Tool.query.get_or_404(tool_id)
    if tool.owner_id != owner.id:
        flash('Invalid request.', 'danger')
        return redirect(url_for('tools.public_inventory', share_token=share_token))

    guest_name = request.form.get('guest_name', '').strip()
    guest_email = request.form.get('guest_email', '').strip()
    if not guest_name or not guest_email:
        flash('Name and email are required.', 'danger')
        return redirect(url_for('tools.public_inventory', share_token=share_token))

    reservation = Reservation(
        tool_id=tool.id,
        guest_name=guest_name,
        guest_email=guest_email,
        status='pending',
    )
    db.session.add(reservation)
    db.session.commit()
    flash(f'Reservation request submitted for "{tool.name}".', 'success')
    return redirect(url_for('tools.public_inventory', share_token=share_token))

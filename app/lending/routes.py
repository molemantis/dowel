from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from ..models import db, Tool, Checkout, Reservation
from . import lending_bp


@lending_bp.route('/checkout/<int:tool_id>', methods=['GET', 'POST'])
@login_required
def checkout(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    if tool.owner_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('tools.index'))

    if not tool.is_available:
        flash('Tool is already checked out.', 'warning')
        return redirect(url_for('tools.detail', tool_id=tool.id))

    if request.method == 'POST':
        borrower_name = request.form.get('borrower_name', '').strip()
        borrower_email = request.form.get('borrower_email', '').strip()
        borrower_phone = request.form.get('borrower_phone', '').strip()
        notes = request.form.get('notes', '').strip()

        try:
            duration = int(request.form.get('duration', 7))
            duration = max(1, min(90, duration))
        except ValueError:
            duration = 7

        if not borrower_name:
            flash('Borrower name is required.', 'danger')
            return render_template('lending/checkout.html', tool=tool)

        due_at = datetime.utcnow() + timedelta(days=duration)
        checkout_obj = Checkout(
            tool_id=tool.id,
            borrower_name=borrower_name,
            borrower_email=borrower_email or None,
            borrower_phone=borrower_phone or None,
            due_at=due_at,
            notes=notes or None,
            checkout_duration_days=duration,
        )
        db.session.add(checkout_obj)
        db.session.commit()
        flash(f'"{tool.name}" checked out to {borrower_name}. Due {due_at.strftime("%b %d, %Y")}.', 'success')
        return redirect(url_for('tools.detail', tool_id=tool.id))

    return render_template('lending/checkout.html', tool=tool)


@lending_bp.route('/return/<int:checkout_id>', methods=['POST'])
@login_required
def return_tool(checkout_id):
    checkout_obj = Checkout.query.get_or_404(checkout_id)
    tool = checkout_obj.tool
    if tool.owner_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('tools.index'))

    if checkout_obj.returned_at:
        flash('Already returned.', 'info')
        return redirect(url_for('tools.detail', tool_id=tool.id))

    checkout_obj.returned_at = datetime.utcnow()

    # Notify first pending reservation
    first_res = tool.reservations.filter_by(status='pending').order_by(Reservation.created_at).first()
    if first_res:
        first_res.status = 'notified'
        first_res.notified_at = datetime.utcnow()

    db.session.commit()
    flash(f'"{tool.name}" marked as returned.', 'success')
    return redirect(url_for('tools.detail', tool_id=tool.id))


@lending_bp.route('/history')
@login_required
def history():
    # All checkouts for tools owned by current user
    tools = Tool.query.filter_by(owner_id=current_user.id).all()
    tool_ids = [t.id for t in tools]
    checkouts = (Checkout.query
                 .filter(Checkout.tool_id.in_(tool_ids))
                 .order_by(Checkout.checked_out_at.desc())
                 .all())
    return render_template('lending/history.html', checkouts=checkouts)


@lending_bp.route('/reserve/<int:tool_id>', methods=['POST'])
@login_required
def reserve(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    if tool.is_available:
        flash('Tool is available — just check it out!', 'info')
        return redirect(url_for('tools.detail', tool_id=tool.id))

    existing = Reservation.query.filter_by(
        tool_id=tool.id, user_id=current_user.id, status='pending'
    ).first()
    if existing:
        flash('You already have a reservation for this tool.', 'info')
        return redirect(url_for('tools.detail', tool_id=tool.id))

    res = Reservation(tool_id=tool.id, user_id=current_user.id, status='pending')
    db.session.add(res)
    db.session.commit()
    flash(f'Reservation added for "{tool.name}".', 'success')
    return redirect(url_for('tools.detail', tool_id=tool.id))


@lending_bp.route('/cancel-reservation/<int:res_id>', methods=['POST'])
@login_required
def cancel_reservation(res_id):
    res = Reservation.query.get_or_404(res_id)
    if res.tool.owner_id != current_user.id and res.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('tools.index'))
    res.status = 'cancelled'
    db.session.commit()
    flash('Reservation cancelled.', 'info')
    return redirect(url_for('tools.detail', tool_id=res.tool_id))

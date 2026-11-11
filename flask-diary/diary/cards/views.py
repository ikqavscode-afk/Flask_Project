"""Страницы карточек: список, просмотр, создание, редактирование, удаление."""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from . import services
from .validation import validate_card

bp = Blueprint('cards', __name__)


def _validated_form():
    return validate_card(
        request.form.get('title'),
        request.form.get('subtitle'),
        request.form.get('text'),
    )


def _flash_errors(errors):
    for error in errors:
        flash(error, 'error')


@bp.route('/')
@login_required
def index():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    pagination = services.search_cards(
        current_user.id, q, page, current_app.config['CARDS_PER_PAGE']
    )
    return render_template('cards/index.html', cards=pagination.items, pagination=pagination, q=q)


@bp.route('/card/<int:id>')
@login_required
def detail(id):
    card = services.get_user_card_or_404(id, current_user.id)
    return render_template('cards/card.html', card=card)


@bp.route('/create')
@login_required
def create_shortcut():
    return redirect(url_for('cards.create'))


@bp.route('/form_create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        data, errors = _validated_form()
        if errors:
            _flash_errors(errors)
            return render_template('cards/create.html', form=request.form), 400

        card = services.create_card(current_user.id, data)
        current_app.logger.info('card created id=%s user_id=%s', card.id, current_user.id)
        flash('Карточка создана!', 'success')
        return redirect(url_for('cards.index'))

    return render_template('cards/create.html', form=None)


@bp.route('/card/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    card = services.get_user_card_or_404(id, current_user.id)

    if request.method == 'POST':
        data, errors = _validated_form()
        if errors:
            _flash_errors(errors)
            return render_template('cards/edit.html', card=card, form=request.form), 400

        services.update_card(card, data)
        current_app.logger.info('card updated id=%s user_id=%s', card.id, current_user.id)
        flash('Карточка обновлена!', 'success')
        return redirect(url_for('cards.detail', id=card.id))

    return render_template('cards/edit.html', card=card, form=None)


@bp.route('/card/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    card = services.get_user_card_or_404(id, current_user.id)
    card_id = services.delete_card(card)
    current_app.logger.info('card deleted id=%s user_id=%s', card_id, current_user.id)
    flash('Карточка удалена', 'success')
    return redirect(url_for('cards.index'))

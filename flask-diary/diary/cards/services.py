"""Бизнес-логика карточек. Не зависит от запросов и шаблонов."""

from ..extensions import db
from ..models import Card


def search_cards(user_id, query_text, page, per_page):
    """Карточки пользователя (новые сверху), опционально с поиском без учёта регистра."""
    query = Card.query.filter_by(user_id=user_id)
    if query_text:
        pattern = f'%{query_text}%'
        query = query.filter(
            Card.title.ilike(pattern) | Card.subtitle.ilike(pattern) | Card.text.ilike(pattern)
        )
    return query.order_by(Card.id.desc()).paginate(page=page, per_page=per_page, error_out=False)


def get_user_card_or_404(card_id, user_id):
    """Карточка, принадлежащая пользователю; чужая или несуществующая даёт 404."""
    return Card.query.filter_by(id=card_id, user_id=user_id).first_or_404()


def create_card(user_id, data):
    card = Card(
        title=data['title'],
        subtitle=data['subtitle'],
        text=data['text'],
        user_id=user_id,
    )
    db.session.add(card)
    db.session.commit()
    return card


def update_card(card, data):
    card.title = data['title']
    card.subtitle = data['subtitle']
    card.text = data['text']
    db.session.commit()
    return card


def delete_card(card):
    card_id = card.id
    db.session.delete(card)
    db.session.commit()
    return card_id

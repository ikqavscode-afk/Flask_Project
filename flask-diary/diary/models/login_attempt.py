from ..extensions import db


class LoginAttempt(db.Model):
    """Неудачная попытка входа (для ограничения перебора паролей).

    Хранится в базе, а не в памяти: процессов gunicorn несколько, и счётчик
    в памяти одного из них можно было бы обойти.
    """
    __tablename__ = 'login_attempt'
    __table_args__ = (db.Index('ix_login_attempt_key_created', 'key', 'created_at'),)

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

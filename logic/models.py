import datetime as dt
import sqlalchemy as sa
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Clients(Base):
    __tablename__ = 'clients'

    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    surname = sa.Column(sa.String(255))
    city = sa.Column(sa.String(255))
    gender = sa.Column(sa.String(1))
    __table_args__ = (CheckConstraint(gender.in_(['М', 'Ж'])),)

    favourites_persons = relationship('Persons', secondary='favourites',
                                      back_populates='favourites_clients')


class Queries(Base):
    __tablename__ = 'queries'

    # добавить констрейнт на уникальный набор параметров?
    id = sa.Column(sa.BigInteger, primary_key=True)
    client_id = sa.Column(sa.BigInteger,
                          sa.ForeignKey('clients.id', ondelete='NO ACTION'),
                          nullable=False)
    query_date = sa.Column(sa.DateTime, default=dt.datetime.now)
    age_from = sa.Column(sa.Integer, default=16)
    age_to = sa.Column(sa.Integer, default=99)
    city = sa.Column(sa.String(255))
    gender = sa.Column(sa.String(1))

    __table_args__ = (CheckConstraint(gender.in_(['М', 'Ж'])),
                      CheckConstraint(age_from > 15),
                      CheckConstraint(age_to < 100),)
    candidates_persons = relationship('Persons', secondary='candidates',
                                      back_populates='candidates_queries')


class Persons(Base):
    __tablename__ = 'persons'

    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    surname = sa.Column(sa.String(255))
    profile_url = sa.Column(sa.String(2000))
    photo_1_link = sa.Column(sa.String(2000))
    photo_2_link = sa.Column(sa.String(2000))
    photo_3_link = sa.Column(sa.String(2000))

    favourites_clients = relationship('Clients', secondary='favourites',
                                      back_populates='favourites_persons')
    candidates_queries = relationship('Queries', secondary='candidates',
                                      back_populates='candidates_persons')


favourites = sa.Table(
    'favourites', Base.metadata,
    sa.Column('client_id', sa.BigInteger,
              sa.ForeignKey('clients.id', ondelete='NO ACTION'),
              nullable=False),
    sa.Column('person_id', sa.BigInteger,
              sa.ForeignKey('persons.id', ondelete='NO ACTION'),
              nullable=False)
)

candidates = sa.Table(
    'candidates', Base.metadata,
    sa.Column('query_id', sa.BigInteger,
              sa.ForeignKey('queries.id', ondelete='NO ACTION'),
              nullable=False),
    sa.Column('person_id', sa.BigInteger,
              sa.ForeignKey('persons.id', ondelete='NO ACTION'),
              nullable=False)
)

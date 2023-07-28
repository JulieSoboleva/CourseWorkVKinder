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

    persons = relationship('Favourites', back_populates='client')


class Queries(Base):
    __tablename__ = 'queries'

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
    persons = relationship('Candidates', back_populates='query')


class Persons(Base):
    __tablename__ = 'persons'

    id = sa.Column(sa.BigInteger, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False)
    surname = sa.Column(sa.String(255))
    profile_url = sa.Column(sa.String(2000))
    photo_1_link = sa.Column(sa.String(2000))
    photo_2_link = sa.Column(sa.String(2000))
    photo_3_link = sa.Column(sa.String(2000))

    queries = relationship('Candidates', back_populates='person')
    clients = relationship('Favourites', back_populates='person')


class Candidates(Base):
    __tablename__ = 'candidates'

    query_id = sa.Column(sa.BigInteger,
                         sa.ForeignKey('queries.id', ondelete='CASCADE'),
                         primary_key=True)
    person_id = sa.Column(sa.BigInteger,
                          sa.ForeignKey('persons.id', ondelete='CASCADE'),
                          primary_key=True)
    query = relationship('Queries', back_populates='persons')
    person = relationship('Persons', back_populates='queries')


class Favourites(Base):
    __tablename__ = 'favourites'

    client_id = sa.Column(sa.BigInteger,
                          sa.ForeignKey('clients.id', ondelete='CASCADE'),
                          primary_key=True)
    person_id = sa.Column(sa.BigInteger,
                          sa.ForeignKey('persons.id', ondelete='CASCADE'),
                          primary_key=True)
    client = relationship('Clients', back_populates='persons')
    person = relationship('Persons', back_populates='clients')

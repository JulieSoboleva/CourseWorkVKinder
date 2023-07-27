import sqlalchemy as sa
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from .models import Clients, Base, Queries, Persons, Favourites, Candidates


class Service:
    def __init__(self):
        self.engine = sa.create_engine('postgresql://postgres:postgres@'
                                       'localhost:5432/vkinder_db')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def recreate_tables(self):
        Base.metadata.drop_all(self.engine)
        print('Таблицы удалены')
        Base.metadata.create_all(self.engine)
        print('Таблицы созданы')

    def add_client(self, vk_id, first_name, last_name, city, gender):
        client = self.session.query(Clients).filter_by(id=vk_id).first()
        if client is not None:
            print(f'Клиент с id = {vk_id} уже есть в БД')
            return
        client = Clients(id=vk_id, name=first_name, surname=last_name,
                         city=city, gender=gender)
        self.session.add(client)
        self.session.commit()
        print(f'Клиент с id = {vk_id} записан в БД')

    def has_query(self, client_id, gender, city, age_from, age_to):
        query = self.session.query(Queries).filter(
            and_(Queries.client_id == client_id, Queries.city == city,
                 Queries.gender == gender, Queries.age_from == age_from,
                 Queries.age_to == age_to)).first()
        if query is not None:
            print('Запрос с такими параметрами уже есть в БД.')
            return query.id
        return 0

    def add_query(self, client_id, gender, city, age_from=None, age_to=None):
        query = Queries(client_id=client_id, age_from=age_from, age_to=age_to,
                        city=city, gender=gender)
        self.session.add(query)
        self.session.commit()
        print('Запрос сохранён в БД')
        return query.id

    def add_persons(self, query_id, persons: list):
        for person in persons:
            if self.has_person(person['id']):
                self.add_candidate_link(person['id'], query_id)
            else:
                self.add_person(query_id, person)

    def add_person(self, query_id, person):
        candidate = Persons(id=person['id'], name=person['name'],
                            surname=person['surname'],
                            profile_url=person['url'],
                            photo_1_link=person['photos'][0],
                            photo_2_link=person['photos'][1]
                            if len(person['photos']) > 1 else None,
                            photo_3_link=person['photos'][2]
                            if len(person['photos']) > 2 else None)
        self.session.add(candidate)
        link = Candidates(query_id=query_id)
        link.person = candidate
        candidate.queries.append(link)
        self.session.add(link)
        self.session.commit()

    def has_person(self, person_id) -> bool:
        query = self.session.query(Persons).filter_by(id=person_id).count()
        if query == 1:
            print('Человек с такими vk_user_id уже есть в БД.')
            return True
        return False

    def add_candidate_link(self, person_id, query_id):
        link = Candidates(query_id=query_id, person_id=person_id)
        self.session.add(link)
        self.session.commit()

    def add_to_favourites(self, client_id, person_id):
        try:
            link = Favourites(client_id=client_id, person_id=person_id)
            self.session.add(link)
            self.session.commit()
        except IntegrityError:
            return

    def delete_from_candidates(self, query_id, person_id):
        link = self.session.query(Candidates).filter(
            and_(Candidates.query_id == query_id,
                 Candidates.person_id == person_id)).first()
        self.session.delete(link)
        self.session.commit()

    def get_persons(self, query_id) -> list:
        result = self.session.query(Persons) \
            .join(Candidates, and_(Candidates.query_id == query_id,
                                   Persons.id == Candidates.person_id)).all()
        if result is None:
            print('Не нашёл ни одного кандидата, связанного с этим запросом.')
            return []
        pretendents = []
        for person in result:
            pretendents.append({
                'id': person.id,
                'name': person.name,
                'surname': person.surname,
                'url': person.profile_url,
                'photos': [person.photo_1_link,
                           person.photo_2_link,
                           person.photo_3_link]})
        return pretendents

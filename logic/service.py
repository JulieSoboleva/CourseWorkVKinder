import sqlalchemy as sa
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from .models import Clients, Base, Queries, Persons, Favourites, Candidates


class Service:

    def __init__(self):
        self.engine = sa.create_engine('postgresql://postgres:postgres@'
                                       'localhost:5432/vkinder_db')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def drop_tables(self):
        Base.metadata.drop_all(self.engine, )
        print('Таблицы удалены')

    def create_tables(self):
        Base.metadata.create_all(self.engine)
        print('Таблицы созданы')

    def find_client(self, vk_id) -> bool:
        client = self.session.query(Clients).filter_by(id=vk_id).first()
        if client is not None:
            print(f'Клиент с id = {vk_id} уже есть в БД')
            return True
        return False

    def add_client(self, vk_id, first_name, last_name, city, gender):
        client = Clients(id=vk_id, name=first_name, surname=last_name,
                         city=city, gender=gender)
        self.session.add(client)
        self.session.commit()
        print(f'Клиент с id = {vk_id} записан в БД')

    def get_last_query(self, client_id) -> int:
        query = self.session.query(Queries).filter_by(client_id=client_id).\
            order_by(Queries.query_date.desc()).first()
        if query is None:
            return 0
        return query.id

    def get_query_params(self, query_id) -> str:
        result = self.session.query(Queries).filter_by(id=query_id).first()
        if result is None:
            return ''
        return f'Параметры запроса:\n' \
               f'{"мужчина" if result.gender == "М" else "женщина"}, ' \
               f'возраст: {result.age_from} - {result.age_to}, {result.city}'

    def get_queries(self, client_id) -> str:
        queries = self.session.query(Queries).filter_by(client_id=client_id).\
            order_by(Queries.query_date.desc()).all()
        if queries is None:
            return ''
        result = ''
        for item in queries:
            result += f'№{item.id} - ' \
                      f'{"мужчина" if item.gender == "М" else "женщина"}, ' \
                      f'возраст: {item.age_from} - {item.age_to}, {item.city}\n'
        return result

    def has_query(self, client_id, gender, city, age_from, age_to) -> int:
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
                            if len(person['photos']) > 1 else '',
                            photo_3_link=person['photos'][2]
                            if len(person['photos']) > 2 else '')
        self.session.add(candidate)
        link = Candidates(query_id=query_id)
        link.person = candidate
        candidate.queries.append(link)
        self.session.add(link)
        self.session.commit()

    def has_person(self, person_id) -> bool:
        query = self.session.query(Persons).filter_by(id=person_id).count()
        if query == 1:
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

    def get_persons(self, query_id, client_id) -> list:
        result = self.session.query(Persons). \
            join(Candidates, and_(Candidates.query_id == query_id,
                                   Persons.id == Candidates.person_id)). \
            join(Favourites, and_(Favourites.person_id == Persons.id,
                                  Favourites.client_id == client_id),
                 isouter=True).where(Favourites.client_id == None).all()
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

    def get_favourites(self, client_id, query_id) -> list:
        results = self.session.query(Persons.name, Persons.surname,
                                     Persons.profile_url). \
            join(Candidates, and_(Candidates.person_id == Persons.id,
                                  Candidates.query_id == query_id)). \
            join(Favourites, and_(Favourites.person_id == Persons.id,
                                  Favourites.client_id == client_id)).all()
        if results is None:
            return []
        str_list = []
        for row in results:
            str_list.append(f'{row.name} {row.surname}\n{row.profile_url}')
        return str_list

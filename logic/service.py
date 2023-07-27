import sqlalchemy as sa
from sqlalchemy import or_, and_
from sqlalchemy.orm import sessionmaker
from .models import Clients, Base, Queries, Persons, favourites, candidates


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
        client = self.session.query(Queries).filter_by(id=vk_id).first()
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
            and_(Queries.city == city, Queries.gender == gender,
                 Queries.age_from == age_from, Queries.age_to == age_to)) \
            .first()
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

    def add_person(self, vk_user_id, first_name, last_name, city, url, photos):
        person = Persons(vk_id=vk_user_id, name=first_name, surname=last_name,
                         # age=age, gender=gender, url  city=city,
                         photo_1_link=photos[0], photo_2_link=photos[1], photo_3_link=photos[2])
        self.session.add(person)
        # self.session.query(Persons).folter_by(id=person.id).update({
        #     'photo_1_link': photos[0],
        #     'photo_2_link': photos[1],
        #     'photo_3_link': photos[2]
        # })
        self.session.commit()
        return person.id

    def get_persons(self, query_id):
        return []




    # client_id = service.add_client(12345, 'Иван')
    # service.add_query(client_id, 'Ж', 'Москва')
    # person_id = service.add_person(654321, 'Алла', 'Иванова', '')


from collections import Counter

import numpy as np
import pandas
import vk_api


class VkParserModel:
    """
    Основной класс для парсинга Вк.
    """

    def __init__(self, login, password):
        """
        Конструктор класса.
        :param login: логин
        :param password: пароль
        """
        self.session = vk_api.VkApi(login=login, password=password)
        self.session.auth()
        self.vk = self.session.get_api()

    def _insert_into_results(self, req_context: list):
        """
        Служебный метод для заноса промежуточных результатов в итоговый список.
        :param req_context: список промежуточных результатов
        :return: результирующий список
        """
        result = []
        for part_info in req_context:
            if len(part_info) > 0:
                result += part_info
        return result

    def _execute_all(self, type_query: str, count_elements, **kwargs):
        """
        Служебный метод, позволяющий получать все необходимые объекты (посты, комментарии, пользователей.)
        :param type_query: тип запроса. Передаётся в формате *метод vk_api*. Пример: wall.getComments
        :param count_elements: общее количество объектов для получения
        :param kwargs: параметры необходимые для запроса.
        :return: список всех объектов
        """
        result = []

        while_count = count_elements // 1100 + 1
        params = ''
        for key, value in kwargs.items():
            if type(value) is str:
                params += f'"{key}": "{value}",'
            else:
                params += f'"{key}": {str(value)},'
        str_query = f'members.push(API.{type_query}(' + '{' + f'{params}"offset": offset, "fields": ' + '""})["items"]);'

        def code(offset=0):
            query = '''
               var i = 0;
               var members = [];
               var offset = ''' + str(offset) + ''';
               while(i < 11){
                  ''' + str_query + '''
                   i = i + 1;
                   offset = offset + 100;
               }
               return members;
               '''
            return query

        offset = 0
        ku = 0
        while ku < while_count:
            req_context = self.vk.execute(code=code(offset))
            offset += 1100
            ku += 1
            result += self._insert_into_results(req_context)
        return result

    def _check_id_group(self, id_groups: list) -> list:
        """
        Служебный метод предпроцессинга идентификаторов групп
        для приведения к одному формату.
        :param id_groups: Список идентификаторов
        :return: список идентификаторов в установленом формате: либо club18****, либо короткое имя группы.
        """
        id_groups_out = [str(id_group) for id_group in id_groups]
        return id_groups_out


class VkParsingUsers(VkParserModel):
    """
    Парсинг пользователей групп и получение общих пользователей.
    """

    def __init__(self, login=None, password=None):
        if login and password:
            VkParserModel.__init__(self, login, password)
            return
        VkParserModel.__init__(self)

    def get_common_users(self, groups: list, write_file: bool = False, name_file: str = 'out.xlsx') -> list:
        """
        Получение общих пользователей групп.
        :param groups: список идентификаторов групп
        :return: Список общих id-пользователей
        """
        new_groups = self._check_id_group(groups)
        id_users = self.__get_group_users(new_groups)
        id_names = self.__get_name_group(new_groups)
        common_users = self.__get_common_users(id_users)
        if write_file:
            self.__write_file(id_users, id_names, name_file)
        return common_users

    def __get_group_users(self, groups: list) -> dict:
        """
        Служебный метод для вывода словаря
        :param groups: группы.
        :return: словарь - key   - id - group
                           value - list with users
        """
        id_users = dict()
        for group in groups:
            id_users[group] = self.get_users_group(group)
        return id_users

    def __get_all_users(self, id_users: dict) -> list:
        """
        Служебный метод для получения всех уникальных поьзователей.
        :param id_users: словарь key - id группы
                                 value - список пользователей
        :return: список уникальных пользователей
        """
        all_users = None
        for index, value in enumerate(id_users.values()):
            if index == 0:
                all_users = np.array(value)
            all_users = np.union1d(all_users, np.array(value))
        return all_users.tolist()

    def __get_name_group(self, groups: list) -> dict:
        """
        Служебный метод, получения названия групп.
        :param groups: список идентификаторов групп.
        :return: словарь - key   - id group
                           value - name group
        """
        id_name = dict()
        for group in groups:
            id_name[group] = self.vk.groups.getById(group_id=group)[0]['name']  # получение названия группы
        return id_name

    def __get_common_users(self, id_groups: dict) -> list:
        """
        Служебный метод для пересечения всех списков и получения общих пользователей.
        :param id_groups: словарь - id - users
        :return: список общих пользователей
        """
        inter_users = None
        for index, key in enumerate(id_groups.keys()):
            if index == 0:
                inter_users = np.array(id_groups[key])
            inter_users = np.intersect1d(inter_users, np.array(id_groups[key]))  # пересечение при помощи numpy
        return inter_users.tolist()

    def __write_file(self, dict_id_users: dict, dict_id_names: dict, name_file: str):
        """
        Служебный метод, который записывает всех пользователей в один файл.
        :param name_file: Название выходного файла. По умолчанию: "out.xlsx"
        :param dict_id_users: словарь key   - id - group
                                      value - list with users
        :param dict_id_names: словарь - key   - id group
                              value - name group
        :return: Происходит запись файла.
        """
        all_users = list()
        for value in dict_id_users.values():
            all_users += value
        counter = Counter(all_users)
        not_1 = list()
        for i in counter:
            if counter[i] != 1:
                not_1.append(i)
        names_columns = list(dict_id_names.keys())
        df = pandas.DataFrame(columns=names_columns, index=not_1)
        df = df.fillna(0)
        for user in not_1:
            for key in dict_id_names:
                if user in dict_id_users[key]:
                    df.loc[user, key] = 1
        df['sum'] = df.sum(axis=1)
        df.to_excel(name_file)
        return

    def get_users_group(self, id_group: str or int) -> list:
        """
        Получение айдишников пользователей группы вк.
        :param id_group: ид группы
        :return: спсисок id - пользователей
        """
        group_info = self.vk.groups.getById(group_id=id_group)
        group_id = group_info[0]['id']
        count_members = self.vk.groups.getMembers(group_id=group_id, count=0)['count']  # число участников в группе
        result = self._execute_all(type_query='groups.getMembers', count_elements=count_members, group_id=group_id)
        return result


class VkParsingComment(VkParserModel):
    """
    Класс для работы с коментариями и поиска нужных коментариев.
    """

    def __init__(self, login=None, password=None):
        if login and password:
            VkParserModel.__init__(self, login, password)
            return
        VkParserModel.__init__(self)

    def get_posts_in_wall(self, id_group: int, limit: int = 100) -> list:
        """
        Получение постов группы.
        :param id_group: ид группы
        :param limit: количество первых постов для получения. По умолчанию: -1 - все посты
        :return: список постов
        """
        count_posts = limit  # количество первых постов
        result = list()
        while_count = count_posts // 1100  # количество подходов по 1100 постов
        last_query_count = count_posts % 1100  # количество в последнем подходе если < 1100

        def code(offset=0, count_post=1100):
            query = f'''
                var i = 0;
                var members = [];
                var offset = ''' + str(offset) + ''';
                var a = ''' + str(count_post) + ''' / 100;
                var b = ''' + str(count_post) + ''' % 100;
                while(i < a){
                    members.push(API.wall.get({"owner_id": ''' + str(id_group) + ''', "count": 100, "offset": offset, "fields": ""})["items"]);
                    i = i + 1;
                    offset = offset + 100;
                }
                if (b > 0) {
                    members.push(API.wall.get({"owner_id": ''' + str(id_group) + ''', "count": b, "offset": offset, "fields": ""})["items"]);
                }
                return members;
                '''
            return query

        offset = 0
        ku = 0
        while ku < while_count:
            req_context = self.vk.execute(code=code(offset))  # запрос
            offset += 1100
            ku += 1
            result += self._insert_into_results(req_context)
        if last_query_count > 0:
            req_context = self.vk.execute(code=code(offset, count_post=last_query_count))
            result += self._insert_into_results(req_context)
        return result

    def __transform_result(self, dict_keywords: dict) -> list:
        """
        Служебный метод преобразования комментариев в удобный вид: ссылка: текст.
        :param dict_keywords: список всех комментариев
        :return: список преобразованных словарей
        """
        good_result = []
        for keyword, comments in dict_keywords.items():
            transform_comment = {}
            for comment in comments:
                url = f'https://vk.com/wall{str(comment["owner_id"])}_{str(comment["post_id"])}?reply={str(comment["id"])}'
                if len(comment['parents_stack']) != 0:
                    url += '&thread=' + str(comment['parents_stack'][0])
                transform_comment[
                    'url'] = url
                transform_comment['text'] = comment['text']
                transform_comment['keyword'] = keyword
                good_result.append(transform_comment)
                transform_comment = {}
        return good_result

    # можно попробовать припелить многопототочность!!!!
    def find_bad_comment(self, comments: list, words_for_find: list):
        """
        Метод для поиска коментариев по ключевым словам.
        :param comments: список коментариев, полученных из метода get_comments_group, каждый коментарий - json.
        :param words_for_find: набор ключевых слов для поиска коментариев с этими словами.
        :return: список коментариев
        """
        results = {keyword: [] for keyword in words_for_find}
        for comment in comments:
            for word in words_for_find:
                success = word.lower() in comment['text'].lower()
                if success:
                    results[word].append(comment)
        results = self.__transform_result(results)
        return results

    def find_comment_id(self, comments: list, id_user: str or list):
        """
        Метод для поиска коментариевконкретного пользователя.
        :param comments: список всех коментариев
        :param id_user: id пользователя
        :return: список коментариев пользователя
        """
        list_id_user = []
        if type(id_user) == str:
            list_id_user.append(id_user)
        else:
            list_id_user = id_user
        results = {id_user: [] for id in list_id_user}
        for comment in comments:
            for id in list_id_user:
                success = id == str(comment['from_id'])
                if success:
                    results[id].append(comment)
        results = self.__transform_result(results)
        return results

    def get_comments_group(self, id_group: str, limit_posts: int = 100, subcoment: bool = False):
        """
        Получение коментариев для каждого поста в группе.
        :param id_group: id - группы.
        :param limit_posts: количество просматриваемых постов.
        :param subcoment: осуществялть поиск в подкоментариях или нет. По умолчанию False.
        :return:
        """
        all_comments = []
        group_info = self.vk.groups.getById(group_id=id_group)  # получение информции о группе
        group_id = - group_info[0]['id']
        posts = self.get_posts_in_wall(group_id, limit_posts)
        for post in posts:
            post_id = post['id']
            count_comments = post['comments']['count']
            d = self._execute_all(type_query='wall.getComments', count_elements=count_comments,
                                  owner_id=group_id, post_id=post_id,
                                  count=100)
            all_comments += d
            if subcoment:
                comment_with_subcoment = list(filter(lambda x: x['thread']['count'] != 0, d))
                for comment in comment_with_subcoment:
                    id_comment = comment['id']
                    all_comments_ = self._execute_all(type_query='wall.getComments', count_elements=count_comments,
                                                      owner_id=group_id, post_id=post_id, count=100,
                                                      comment_id=id_comment)
                    all_comments += all_comments_
        return all_comments

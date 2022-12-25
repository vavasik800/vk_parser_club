# vk_parser_club
Проект предназначен для парсинга социальной сети ВКонтакте.
Состоит из 3 основынх файлов:
  1. ParsingClassVk.py - модуль содержащий классы для парсинга групп Вк.
      - VkParsingUsers.get_users_group(id_group) - позволяет получить всех пользователей группы с открытыми подписчиками
      - VkParsingUsers.get_common_users(groups, write_file, name_file) - позволяет выделить общих пользователей нескольких групп и вывести результат в файл .xlsx
      - VkParsingComment.get_posts_in_wall(id_group, limit) - позволяет получить заданное число постов указанной группы
      - VkParsingComment.get_comments_group(id_group, limit_posts, subcoment) - позволяет получить все коментарии и подкоментарии указанного числа постов 
      - VkParsingComment.find_comment_id(comments, id_user) - поиск среди найденных коментариев, коментариев определенного пользователя 
      - VkParsingComment.find_bad_comment(comments, words_for_find): поиск среди найденных коментариев, коментариев с определенными ключевыми словами
   2. main.py - модуль, демонстрирующий возможности указанных выше функций
   3. config.py - файл с настройками для аутентификации пользователя и параметров для методов

requirements:
  - numpy;
  - pandas;
  - vk_api.

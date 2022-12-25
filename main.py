from ParsingClassVk import VkParsingComment, VkParsingUsers
import config


def main():
    list_groups = config.GROUPS
    list_keywords = config.KEYWORDS
    group = config.GROUP
    login = config.LOGIN
    password = config.PASSWORD
    id_user = config.ID_USER
    vk_groups = VkParsingUsers(login=login, password=password)
    a = vk_groups.get_users_group(group)
    d = vk_groups.get_common_users(list_groups, write_file=True)
    vk_comment = VkParsingComment(login=login, password=password)
    d = vk_comment.get_comments_group(group, limit_posts=50, subcoment=True)
    result = vk_comment.find_bad_comment(d, list_keywords)
    list_comment = vk_comment.find_comment_id(d, id_user)
    for comment in result:
        print(comment['url'])
        print(comment['text'])
        print(comment['keyword'])
        print('___________________________________________')
    return


if __name__ == "__main__":
    main()

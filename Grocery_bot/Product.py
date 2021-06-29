import database_module as db
from pymorphy2 import MorphAnalyzer

morph = MorphAnalyzer()


class Product:
    __category = None
    __name = None
    __id = None
    __urgent = False

    def __init__(self, id: int, name: str, category=None, urgent=None):
        print(f"Product:__init__:\t id={id}, name={name}, category={category}, urgent={urgent}")
        while '&' in name or '%' in name:
            name.replace('%','проц.')
            name.replace('&', ' and ')
            name.replace('  ',' ')
        if urgent is None:
            if 'срочно' in name.lower():
                self.__urgent = True
                name.replace('срочно', '')
                while "  " in name:
                    name.replace('  ', ' ')
        else:
            self.__urgent = urgent
        self.__name = name
        self.__id = id
        if category is None:
            try:
                name = ''.join(morph.parse(i)[0].normal_form if name.isalpha() else str(i) for i in name.split(' '))
            except ValueError:
                name = self.__name
            found = False
            for word in name.split():
                if found:
                    break
                else:
                    ans = db.read_table('category_product', column_name='product', value=word.lower())
                    if len(ans) > 0:
                        found = True
                        self.__category = ans[0][0]
                        break
            if not found:
                self.__category = 'Другое'
        else:
            self.__category = category
    def get_name(self):
        return self.__name
    def get_category(self):
        return self.__category
    def get_button(self):
        if self.__urgent:
            text = '✅❗️' + bool(len(self.__name) > 27) * (self.__name[:27] + '...') + bool(
                len(self.__name) <= 27) * self.__name + '❗️',
        else:
            text = '✅' + bool(len(self.__name) > 31) * (self.__name[:24] + '...') + bool(
                len(self.__name) <= 31) * self.__name
        reply_markup = f'p&{self.__id}'
        return (text, reply_markup)

    def form_family_dict(self, family_name: str):
        lst = db.read_table(family_name)
        print(lst)
        if len(lst)==0:
            return {}
        cat_prod_dict = {}
        categories = []
        for line in lst:
            if line[1] not in categories:
                categories.append(line[1])
        categories.sort()
        if 'Другое' in categories:
            if categories.index('Другое') != len(categories) - 1:
                categories[categories.index('Другое')], categories[-1] = categories[-1], categories[
                    categories.index('Другое')]
        for category in categories:
            cat_prod_dict[category] = []
            for line in lst:
                if line[1] == category:
                    cat_prod_dict[line[1]].append(Product(line[0], line[2], line[1], bool(line[3])))
        return cat_prod_dict

    def form_message_text(self, c_p_dict):
        print('got 2 f_m_t')
        if len(c_p_dict) != 0:
            message = 'Список покупок:\n\n'
            for category in c_p_dict.keys():
                cnt = 1
                message += category + ':\n'
                for product in c_p_dict[category]:
                    message += str(cnt) + ') ' + product.__name + '\n'
                    cnt += 1
        else:
            message='Список пуст'
        return message

    def is_urgent(self):
        return self.__urgent

    def __str__(self):
        return f"\tName - {self.__name}\tCategory - {self.__category}\tid - {self.__id}\turgent - {self.__urgent}"

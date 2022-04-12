import logging

from database_module import Database
from pymorphy2 import MorphAnalyzer
from mytoken import airtable_token, base_id
import datetime

RU_ALPHABET = {'ё', 'е', 'о', 'ь', 'п', 'м', 'ъ', 'ч', 'щ', 'ы', 'ц', 'х', 'р', 'ж', 'ф', 'в', 'с', 'ш', 'д', 'т', 'я',
               'л', 'й', 'а', 'г', 'э', 'и', 'н', ' ', 'к', 'з', 'у','б','ю'}
formatter = '[%(asctime)s] %(levelname)8s --- %(message)s (%(filename)s:%(lineno)s)'
logging.basicConfig(
    filename=f'bot-from-{datetime.datetime.now().date()}.log',
    filemode='w',
    format=formatter,
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.WARNING
)

morph = MorphAnalyzer()
db = Database(airtable_token, base_id)


class Product:
    __category = None
    __name = None
    id = None
    __urgent = False

    def __init__(self, id: int, name: str, category=None, urgent=None):
        # print(f"Product:__init__:\t id={id}, name={name}, category={category}, urgent={urgent}")
        if urgent is None:
            if 'срочно' in name.lower():
                self.__urgent = True
                self.__name = name.lower().replace('срочно', '').capitalize()
                while "  " in self.__name:
                    self.__name = self.__name.replace('  ', ' ')
            else:
                self.__name = name
        else:
            self.__urgent = urgent
            self.__name = name
        self.id = id
        if category is None:
            name_cpy = ''.join(c for c in name.lower() if c in RU_ALPHABET)
            name_inf = set()
            for word in name_cpy.split(' '):
                name_inf.add(morph.parse(word)[0].normal_form)
            #print(name_inf)
            for word in name_inf:
                self.__category = db.category_product.first(formula="({product}=\"" + word + '")')
                if self.__category is not None:
                    break

            if self.__category is None:
                self.__category = 'Другое'
                try:
                    db.other.create({'name': self.__name})
                except Exception:
                    pass
            else:
                self.__category = self.__category['fields']['category']

        else:
            self.__category = category

    def get_name(self):
        return self.__name

    # def change_name(self, new_name):
    #     self.__name = new_name
    #     try:
    #         new_name = ''.join(
    #             morph.parse(i)[0].normal_form if new_name.isalpha() else str(i) + ' ' for i in new_name.split(' '))
    #     except ValueError:
    #         new_name = self.__name
    #     found = False
    #     for word in new_name.split():
    #         if found:
    #             break
    #         else:
    #             ans = db.read_table('category_product', column_name='product', value=word.lower())
    #             if len(ans) > 0:
    #                 found = True
    #                 self.__category = ans[0][0]
    #                 break
    #     if not found:
    #         self.__category = 'Другое'
    #         try:
    #             db.add_record('Other', self.__name)
    #         except Exception:
    #             pass

    def get_database_list(self):
        return [self.id, self.__category, self.__name, self.__urgent]

    def get_category(self):
        return self.__category

    def get_button(self):
        if self.__urgent:
            text = '✅❗️' + bool(len(self.__name) > 27) * (self.__name[:27] + '...') + bool(
                len(self.__name) <= 27) * self.__name + '❗️'
            # print(text)
        else:
            text = '✅' + bool(len(self.__name) > 31) * (self.__name[:24] + '...') + bool(
                len(self.__name) <= 31) * self.__name
        reply_markup = f'p&{self.id}'
        return (text, reply_markup)

    def form_family_dict(self, family_name: str):
        lst = db.products_database.all(formula='({family}="' + family_name + '")')
        # print(lst)
        if lst is None:
            return {}
        cat_prod_dict = {}
        categories = []
        for line in lst:
            if line['fields']['category'] not in categories:
                categories.append(line['fields']['category'])
        categories.sort()
        if 'Другое' in categories:
            if categories.index('Другое') != len(categories) - 1:
                categories[categories.index('Другое')], categories[-1] = categories[-1], categories[
                    categories.index('Другое')]
        for category in categories:
            cat_prod_dict[category] = []
            for line in lst:
                if line['fields']['category'] == category:
                    cat_prod_dict[line['fields']['category']].append(Product(line['fields']['id'],
                                                                             line['fields']['product'],
                                                                             line['fields']['category'],
                                                                             True if line['fields'][
                                                                                         'urgent'] == 'True' else False))
        return cat_prod_dict

    def form_message_text(self, c_p_dict):
        # print('got 2 f_m_t')
        if len(c_p_dict) != 0:
            message = 'Список покупок:\n\n'
            for category in c_p_dict.keys():
                cnt = 1
                message += category + ':\n'
                for product in c_p_dict[category]:
                    try:
                        message += str(cnt) + ') ' + product.__name + '\n'
                    except TypeError:
                        pass
                    cnt += 1
        else:
            message = 'Список пуст'
        return message

    def is_urgent(self) -> bool:
        return self.__urgent

    def __str__(self):
        return f"\tName - {self.__name}\tCategory - {self.__category}\tid - {self.id}\turgent - {self.__urgent}"

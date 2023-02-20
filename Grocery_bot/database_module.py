import pyairtable


class Database:
    def __init__(self, token, base_id):
        self.category_product = pyairtable.Table(token, base_id, "category_product")
        self.users_database = pyairtable.Table(token, base_id, "users_database")
        self.transferring_logins = pyairtable.Table(token, base_id, "transferring_logins")
        self.other = pyairtable.Table(token, base_id, "other")
        self.products_database = pyairtable.Table(token, base_id, "products_database")
        self.families = pyairtable.Table(token, base_id, "families")


# import sqlite3
# import traceback
#
# database_path = 'main_database.db'
# con = sqlite3.connect(database_path)
# cur = con.cursor()
#
#
#
#
# def create_table(table_name: str, column_titles: dict):
#     """
#     Создать таблицу в базе данных, чего не понятного?
#     :param column_titles:
#     :param table_name: ключ - имя, значение - тип
#     """
#
#     cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?",(table_name,))
#     if len(cur.fetchall())==0:
#         cur.execute(f'CREATE TABLE IF NOT EXISTS {table_name}({list(column_titles.keys())[0]} {column_titles[list(column_titles.keys())[0]]});')
#         for i in list(column_titles.keys())[1:]:
#             cur.execute(f'ALTER TABLE {table_name} ADD {i} {column_titles[i]};')
#         con.commit()
#
#
# def add_record(table_name: str, value: iter):
#     """
#     Добавляет запись в таблицу, в случае возникновения ошибки - возвращает её
#     :param table_name:
#     :param value:
#     :return:
#     """
#     cur.execute(f'PRAGMA TABLE_INFO({table_name})')
#     if len(value)==len(cur.fetchall()):
#         try:
#             cur.execute(f'INSERT INTO {table_name} VALUES({("?, "*len(value))[:-2]})',tuple(value))
#             con.commit()
#             return 'Success'
#         except Exception as e:
#             traceback.print_exc()
#             return f'CRITICAL ERROR\n{str(e)}\nОбратитесь к @artem_pas'
#     else:
#         raise IndexError
#
#
# def remove_record(table_name: str, column_name: str, value):
#     """
#     Удаляет запись из таблицы Вывод -> Bool
#     :param table_name:
#     :param column_name:
#     :param value:
#     :return:
#     """
#     if column_name == '*' and value == '*':
#         try:
#             cur.execute(f'DELETE FROM {table_name}')
#         except Exception as e:
#             print("DATABASE: ", str(e))
#             return False
#         con.commit()
#         return True
#     else:
#         try:
#             cur.execute(f'DELETE FROM {table_name} WHERE {column_name} = ?',(value,))
#         except Exception as e:
#             traceback.print_exc()
#             return False
#         con.commit()
#         return True
#
#
# def read_table(table_name: str, column_name=None, value=None):
#     """
#     Читает записи из базы данных, при
#     отсутствии значений у параметров column_name и value
#     возвращает все значения из таблицы
#     :param table_name:
#     :param column_name:
#     :param value:
#     :return:
#     """
#     if column_name is not None and value is not None:
#         cur.execute(f"SELECT * FROM {table_name} WHERE {column_name} = ?",(value,))
#         con.commit()
#         return cur.fetchall()
#     else:
#         cur.execute(f'SELECT * FROM {table_name}')
#
#         try:
#             return cur.fetchall()
#         except UnicodeEncodeError:
#             pass
#
#
# def run_anything(text):
#     cur.execute(text)
#     con.commit()
#     return cur.fetchall()
#
#

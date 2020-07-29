

import sqlite3
import sys
import codecs

database_path = 'main_database.db'
con = sqlite3.connect(database_path)
cur = con.cursor()


def create_table(table_name: str, column_titles: dict):
    """
    Создать таблицу в базе данных, чего не понятного?
    :param column_titles:
    :param table_name: ключ - имя, значение - тип
    """
    print(table_name, column_titles)
    sql = f'CREATE TABLE IF NOT EXISTS {table_name}('
    for i in column_titles:
        sql += i + ' ' + column_titles[i] + ', '
    sql = sql[:-2] + ')'
    cur.execute(sql)
    con.commit()


def add_record(table_name: str, value: list):
    """
    Добавляет запись в таблицу, в случае возникновения ошибки - возвращает её
    :param table_name:
    :param value:
    :return:
    """
    cur.execute(f'PRAGMA TABLE_INFO({table_name})')
    columns_nubmer = len(cur.fetchall())
    try:
        cur.execute(f'INSERT INTO {table_name} VALUES({("?, " * columns_nubmer)[:-2]})', value)
        con.commit()
        return 'Добавление записи в базу данных успешно'
    except Exception as e:
        print(str(e))
        return f'CRITICAL ERROR\n{str(e)}\nОбратитесь к @artem_pas'


def remove_record(table_name: str, column_name: str, value: str):
    """
    Удаляет запись из таблицы, в случае возникновения ошибки - возвращает её
    :param table_name:
    :param column_name:
    :param value:
    :return:
    """
    try:
        cur.execute(f'DELETE FROM {table_name} WHERE {column_name} = {value}')
    except Exception as e:
        print(str(e))
        return f'CRITICAL ERROR\n{str(e)}'
    con.commit()


def read_table(table_name: str, column_name=None, value=None):
    """
    Читает записи из базы данных, при
    отсутствии значений у параметров column_name и value
    возвращает все значения из таблицы
    :param table_name:
    :param column_name:
    :param value:
    :return:
    """
    if column_name is not None and value is not None:
        cur.execute(f"SELECT * FROM {table_name} WHERE {column_name}='{value}'")
        con.commit()
        return cur.fetchall()
    else:
        cur.execute(f'SELECT * FROM {table_name}')
        con.commit()
        try:
            return cur.fetchall()
        except UnicodeEncodeError:
            pass


if __name__ == '__main__':
    print(read_table('category_product','category', 'Мясо'))

import sqlite3
from sqlite3 import Error


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('test.db')
        self.cursor = self.conn.cursor()
        self.create_table()

    def __del__(self):
        self.conn.close()
        print('Connection closed')

    def create_table(self):
        sql_create_table = """CREATE TABLE IF NOT EXISTS data_tab (
                                id integer PRIMARY KEY AUTOINCREMENT,
                                name_id text NOT NULL,
                                name text NOT NULL,
                                season text NOT NULL,
                                episode text NOT NULL,
                                img_source text NOT NULL,
                                tab integer NOT NULL,
                                is_finished boolean NOT NULL,
                                user_comment text
                                ); """
        self.cursor.execute(sql_create_table)
        self.conn.commit()

    def add_data(self, name_id, name, season, episode, img_source, tab, is_finished, user_comment=''):
        try:
            data = "INSERT INTO data_tab " \
                   "(name_id, name, season, episode, img_source, tab, is_finished, user_comment) " \
                   "VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
            self.cursor.execute(data, (name_id, name, season, episode, img_source, tab, is_finished, user_comment))
            self.conn.commit()
        except Error as err:
            print(err)
            return err

    def update_data(self, db_id, name_id, name, season, episode, img_source, is_finished, user_comment):
        try:
            data = "UPDATE data_tab SET name_id = ?, name= ?, season = ?," \
                   " episode = ?, img_source = ?, is_finished = ?, user_comment = ? WHERE id = ?"
            self.cursor.execute(data, (name_id, name, season, episode, img_source, is_finished, user_comment, db_id))
            self.conn.commit()
        except Error as err:
            print(err)
            return err

    def plus_one_episode(self, db_id, episode):
        try:
            data = "UPDATE data_tab SET episode = ? WHERE id = ?"
            self.cursor.execute(data, (episode, db_id))
            self.conn.commit()
        except Error as err:
            print(err)
            return err

    def get_data(self):
        data = "SELECT * FROM data_tab"
        result = self.cursor.execute(data).fetchall()
        return result

    def move_to_archive(self, db_id):
        data = "UPDATE data_tab SET tab = 1 WHERE id = ?"
        self.cursor.execute(data, (db_id,))
        self.conn.commit()

    def move_to_actual(self, db_id):
        data = "UPDATE data_tab SET tab = 0 WHERE id = ?"
        self.cursor.execute(data, (db_id,))
        self.conn.commit()

    def show_db(self):
        print('show db method:')
        data = "SELECT * FROM data_tab"
        result = self.cursor.execute(data).fetchall()
        for row in result:
            print(row)

    def delete_id(self, db_id):
        self.cursor.execute("DELETE FROM data_tab WHERE id=?", (db_id,))
        self.conn.commit()
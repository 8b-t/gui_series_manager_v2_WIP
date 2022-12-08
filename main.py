from kivy.config import Config
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.list import ImageLeftWidget, IRightBodyTouch, ThreeLineAvatarIconListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import Snackbar
import re
import os
import urllib.request

from kivymd.uix.tab import MDTabsBase
from transliterate import translit, detect_language
from database import Database

from myparser_package.myparser import MyParser

Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '1000')
Config.set('graphics', 'minimum_width', '600')
Config.set('graphics', 'minimum_height', '600')
Config.set('graphics', 'resizable', 0)
Config.set('input', 'mouse', 'mouse, multitouch_on_demand')
Config.write()

db = Database()


# preview image local saving
def image_save(url, filename):
    local_path = 'imgs'
    urllib.request.urlretrieve(url, f'{local_path}/{filename}.jpg')


# Main Window UI
class MainWindow(BoxLayout):
    pass


class Tab(MDFloatLayout, MDTabsBase):
    pass


class MyContainer(IRightBodyTouch, MDBoxLayout):
    pass


# list item dot menu header
class MenuHeader(MDBoxLayout):
    header_name = StringProperty()

    def __init__(self, header_name='', **kwargs):
        super().__init__(**kwargs)
        self.header_name = header_name


class LinkImportDialogContent(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_obj = None

    #"Import" button event
    def on_button_click(self, widget):
        if widget.text:
            try:
                self.current_obj = MyParser(widget.text)
                MainApp.data_storage = self.current_obj
                MainApp.snackbar_action(f'Info about {self.current_obj.get_main_title()} uploaded')
            except Exception as err:
                print(err)
                MainApp.snackbar_action(f"[color=#ff5555]Import Failed![/color] {err}", 5)


class ImportDialogContent(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = MainApp.data_storage
        self.on_start_import_d_c()

    def on_start_import_d_c(self):
        if self.data:
            try:
                self.ids.series_name_label.text = self.data.get_main_title()
                self.ids.series_info_label.text = self.data.get_series_info()
                self.ids.series_info_label.hint_text = "Series/Movie Info:"
                self.ids.series_preview_img.source = self.data.get_preview_img()
                self.ids.series_preview_img.color = "1", "1", "1", "1"
                MainApp.snackbar_action(f'Info about {self.data.get_main_title()} uploaded')
            except Exception as err:
                print(err)
                MainApp.snackbar_action(f"[color=#ff5555]Import Failed![/color] {err}", 5)

    # "add to list" button event
    def on_add_to_list_button_click(self):
        if self.data:
            try:
                # converting name of series/movie to acceptable name
                snakecase_name = MainApp.name_to_id_convert(self.data.get_main_title())
                # preview image save TODO: db_id + get_id in name of file
                image_save(self.data.get_preview_img(), snakecase_name)
                img_src = f'imgs/{snakecase_name}.jpg'
                if self.data.is_this_tv_show():
                    season = 'Season: 1'
                    episode = 'Episode: 1'
                else:
                    season = 'Movie'
                    episode = '---'
                db.add_data(snakecase_name, self.data.get_main_title(), season, episode, img_src, 0, 0)
                MainApp.get_running_app().create_list_item(db.cursor.lastrowid, snakecase_name, self.data.get_main_title(),
                                      season, episode, img_src, 0, 0)

                # db.show_db()  # temporary DELETE ME LATER
                # self.current_obj = None  # temporary to prevent second click
                MainApp.clear_storage()
                MainApp.snackbar_action(f'{self.data.get_main_title()} added to Watchlist tab !')
            except Exception as err:
                print(str(err))


# Dialog window
class ListDialogContent(MDBoxLayout):
    # attributes for accessing from kv file
    obj = ObjectProperty()
    id = StringProperty()
    name = StringProperty()
    season = StringProperty()
    episode = StringProperty()
    img_src = StringProperty()
    is_finished = BooleanProperty()
    user_comment = StringProperty()

    def __init__(self, item, **kwargs):
        super().__init__(**kwargs)
        self.obj = item
        self.id = item.list_item_id
        self.name = item.text
        self.season = item.secondary_text.lstrip('Season: ')
        self.episode = item.tertiary_text.lstrip('Episode: ')
        self.img_src = f'imgs/{item.list_item_id}.jpg'
        self.is_finished = True if item.is_finished == 1 else False
        self.user_comment = item.user_comment

    def update_info_from_dialog(self, item):
        # simple filters to prevent None data
        if self.ids.name_text_field.text and self.ids.id_label_dialog.text[4:]:
            item.text = self.ids.name_text_field.text[:70]
            # if id was changed, preview image name also change
            try:
                os.rename(self.img_src, f'imgs/{self.ids.id_label_dialog.text[4:]}.jpg')
                self.img_src = f'imgs/{self.ids.id_label_dialog.text[4:]}.jpg'
            except Exception as err:
                MainApp.snackbar_action(str(err), 5)
            item.list_item_id = self.ids.id_label_dialog.text[4:]
            if self.ids.season_text_field.text and self.ids.episode_text_field.text and \
                    self.ids.season_text_field.text != 'Movie':
                item.secondary_text = f'Season: {self.ids.season_text_field.text[:5]}'
                item.tertiary_text = f'Episode: {self.ids.episode_text_field.text[:70]}'
            else:
                item.secondary_text = 'Movie'
                item.tertiary_text = '---'
            item.user_comment = self.ids.comment_text_field.text[:400]
            item.is_finished = 1 if self.ids.series_state.active else 0
            item.bg_color = (.3, .3, .3, .1) if self.ids.series_state.active else (0, 0, 0, 0)
            db.update_data(item.db_id, item.list_item_id, item.text, item.secondary_text,
                           item.tertiary_text, self.img_src, item.is_finished, item.user_comment)
            # db.show_db()
            MainApp.snackbar_action(f'{item.text} saved')
        else:
            MainApp.snackbar_action("[color=#ff5555]Save Failed![/color] Name and id can't be empty.", 5)

    def on_text_field_validate(self, text):
        if self.ids.name_text_field.text:
            new_id = f'id: {MainApp.name_to_id_convert(text)}'
            self.ids.id_label_dialog.text = new_id


# to avoid weird error's about arguments/param's
class MyLeftWidget(ImageLeftWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Custom widget for list items
class CustomListItem(ThreeLineAvatarIconListItem):
    brief_menu_active = BooleanProperty(False)

    def __init__(self, list_item_id=None, db_id=None, tab_number=0, is_finished=0, user_comment='', **kwargs):
        super().__init__(**kwargs)
        self.list_item_id = list_item_id
        self.db_id = db_id
        self.tab_number = tab_number
        self.is_finished = is_finished
        self.user_comment = user_comment

    def on_kv_post(self, base_widget):
        menu_items = [
            {
                "text": "Edit",
                # "icon": "pencil",
                "viewclass": "DropDownMenuItem",
                "height": dp(46),
                "on_release": lambda list_item=self: self.edit_item(list_item),
            },
            {
                "text": "Move to Archive tab",
                # "icon": "folder-move",
                "viewclass": "DropDownMenuItem",
                "height": dp(46),
                "on_release": lambda list_item=self: self.move_to_tab(list_item),
            },
            {
                "text": "Delete",
                # "icon": "delete",
                "viewclass": "DropDownMenuItem",
                "height": dp(46),
                "on_release": lambda list_item=self: self.delete_item(list_item),
            },
        ]
        brief_menu_items = [
            {
                "name": self.text,
                "viewclass": "BriefMenuContent",
                "height": dp(90),
                "caller_instance": None,
            }
        ]

        self.menu = MDDropdownMenu(
            header_cls=MenuHeader(),
            caller=self.ids.dots_button,
            items=menu_items,
            width_mult=4,
            opening_time=0,
        )

        self.brief_menu = MDDropdownMenu(
            items=brief_menu_items,
            background_color=[0, 0, 0, 0],
            width_mult=3,
            opening_time=0,
            position='center',
        )

    # opening list item side menu with header shortening
    def menu_drop(self, list_item):
        if list_item.tab_number == 1:
            self.menu.items[1]['text'] = 'Move to Watchlist tab'
        if len(list_item.text) > 23:
            self.menu.header_cls.ids.menu_header_label.text = list_item.text[:23] + '...'
        else:
            self.menu.header_cls.ids.menu_header_label.text = list_item.text
        self.menu.header_cls.ids.menu_header_label.tooltip_text = list_item.text
        self.menu.open()

    def brief_menu_drop(self, list_item):
        self.brief_menu.caller = list_item
        self.brief_menu.items[0]['caller_instance'] = list_item
        if list_item.is_finished or list_item.tertiary_text == '---':
            self.brief_menu.items[0]['disable_plus_button'] = True
        else:
            self.brief_menu.items[0]['disable_plus_button'] = False
        self.brief_menu.open()

    # Delete list item
    def delete_item(self, list_item):
        try:
            self.parent.remove_widget(list_item)
            self.menu.dismiss()
            db.delete_id(list_item.db_id)
            MainApp.snackbar_action(f'{list_item.text} deleted')
            os.remove(f'imgs/{list_item.list_item_id}.jpg')
        except Exception as err:
            MainApp.snackbar_action(str(err), 5)

    # Calling edit list item from side menu
    def edit_item(self, list_item):
        self.brief_menu.dismiss()
        MainApp.get_running_app().show_list_item_dialog(list_item)
        self.menu.dismiss()
        MainApp.snackbar_action(f'{list_item.text} edit')

    # Switch watchlist <> archive tabs of list item
    def move_to_tab(self, list_item):
        to_tab = 0
        if list_item.tab_number == 0:
            to_tab = 1
            db.move_to_archive(list_item.db_id)
            MainApp.snackbar_action(f'{list_item.text} moved to Archive tab')
        else:
            db.move_to_actual(list_item.db_id)
            MainApp.snackbar_action(f'{list_item.text} moved to Watchlist tab')
        # children[1].children[0].source Preview Image source
        MainApp.get_running_app().create_list_item(list_item.db_id, list_item.list_item_id, list_item.text,
                                                   list_item.secondary_text, list_item.tertiary_text,
                                                   list_item.children[1].children[0].source, to_tab,
                                                   list_item.is_finished, list_item.user_comment)
        self.parent.remove_widget(list_item)
        self.menu.dismiss()


    def add_one_episode(self):
        self.brief_menu.dismiss()
        tmp = int(self.tertiary_text.lstrip('Episode: ')) + 1
        self.tertiary_text = f'Episode: {tmp}'
        db.plus_one_episode(self.db_id, self.tertiary_text)
        MainApp.snackbar_action(f'+1 episode added to {self.text}')


class MainApp(MDApp):
    # for checking if no active dialog window atm
    list_item_dialog = None
    data_storage = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)



    def build(self):
        Window.top = 30
        Window.left = 200
        self.theme_cls.primary_palette = 'Cyan'
        # Palette's:
        # ['Red', 'Pink', 'Purple', 'DeepPurple', 'Indigo', 'Blue', 'LightBlue', 'Cyan', 'Teal', 'Green',
        # 'LightGreen', 'Lime', 'Yellow', 'Amber', 'Orange', 'DeepOrange', 'Brown', 'Gray', 'BlueGray']
        self.theme_cls.theme_style = 'Dark'
        # Style's :
        # 'Light' or 'Dark'
        # self.theme_cls.primary_hue = "500"
        self.toolbar_menu_items = [
            {
                "text": "Manual Addition",
                "viewclass": "DropDownMenuItem",
                "height": dp(42),
                "on_release": lambda: (MainApp.snackbar_action('Not available at this moment. Work in progress', 5),
                                       self.toolbar_right_menu.dismiss())
            },
            {
                "text": "Import",
                "viewclass": "DropDownMenuItem",
                "height": dp(46),
                "on_release": lambda: (self.show_link_import_dialog(), self.toolbar_right_menu.dismiss()),
            },
        ]
        self.toolbar_right_menu = MDDropdownMenu(
            items=self.toolbar_menu_items,
            background_color=[.1, .1, .1, .9],
            width_mult=4,
            opening_time=.3,
            position='auto',
        )

    # Load all data from db to CustomList
    def on_start(self):
        data = db.get_data()
        for row in data:
            self.create_list_item(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
        # print(self.root.ids.tabs.get_current_tab()) #TODO Make first tab active on start

    # def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
    #     pass

    def create_list_item(self, db_id: int, name_id, name, season, episode,
                         img_source, tab: int, is_finished: int, user_comment=''):
        try:
            if is_finished == 1:
                colorize = (.3, .3, .3, .2)
            else:
                colorize = None
            # creating list items
            item = CustomListItem(
                list_item_id=name_id,
                db_id=db_id,
                text=name,
                secondary_text=season,
                tertiary_text=episode,
                tab_number=tab,
                ripple_scale=0,
                is_finished=is_finished,
                user_comment=user_comment,
                bg_color=colorize,
            )

            # grab avatar image
            image = MyLeftWidget(
                source=img_source,
                size_hint=(None, None),
                size=(dp(52), dp(52)),
                radius=(5, 5, 5, 5),
                pos_hint={"center_y": .4},
            )
            item.add_widget(image)
            if tab == 0:
                self.root.ids.actual_listview.add_widget(item)
            elif tab == 1:
                self.root.ids.archive_listview.add_widget(item)
        except Exception as err:
            MainApp.snackbar_action(f"[color=#ff5555]{str(err)}[/color]", 5)

    def show_list_item_dialog(self, list_item):
        if not self.list_item_dialog:
            self.list_item_dialog = MDDialog(
                title=f'"{list_item.text}":',
                type='custom',
                content_cls=ListDialogContent(list_item),
                auto_dismiss=False,
            )
        self.list_item_dialog.open()

    def show_link_import_dialog(self):
        if not self.list_item_dialog:
            self.list_item_dialog = MDDialog(
                title=f'Import series or movie',
                type='custom',
                content_cls=LinkImportDialogContent(),
                auto_dismiss=False,
            )
        self.list_item_dialog.open()

    def show_import_dialog(self):
        if not self.list_item_dialog:
            self.list_item_dialog = MDDialog(
                #title=f'{MainApp.data_storage.get_main_title()}',
                type='custom',
                content_cls=ImportDialogContent(),
                auto_dismiss=False,
            )
        self.list_item_dialog.open()

    def close_list_item_dialog(self):
        self.list_item_dialog.dismiss()
        self.list_item_dialog = None

    def toolbar_right_menu_drop(self, instance):
        self.toolbar_right_menu.caller = instance
        self.toolbar_right_menu.open()

    @staticmethod
    def clear_storage():
        MainApp.data_storage = None

    # Something like: "Terminator 2: Judgement Day" to "terminator_2_judgement_day"
    @staticmethod
    def name_to_id_convert(name: str):
        try:
            from_language = detect_language(name)
            if from_language:
                to_eng = translit(name, from_language, reversed=True)
                return '_'.join(re.findall(r'[a-z0-9_]+', to_eng.lower()))
            return '_'.join(re.findall(r'[a-z0-9_]+', name.lower()))
        except Exception as err:
            print(str(err))
            return '_'.join(re.findall(r'[a-z0-9_]+', name.lower()))

    # show info on snackbar
    @staticmethod
    def snackbar_action(txt, arg_duration=1):
        snackbar = Snackbar(text=txt,
                            bg_color=[0, 0, 0, .3],
                            duration=arg_duration,
                            font_size='16sp',
                            snackbar_x="8dp",
                            snackbar_y="4dp",
                            )
        snackbar.size_hint_x = (Window.width - (snackbar.snackbar_x * 2)) / Window.width
        snackbar.open()


if __name__ == '__main__':
    MainApp().run()

# Palette's:
# ['Red', 'Pink', 'Purple', 'DeepPurple', 'Indigo', 'Blue', 'LightBlue', 'Cyan', 'Teal', 'Green',
# 'LightGreen', 'Lime', 'Yellow', 'Amber', 'Orange', 'DeepOrange', 'Brown', 'Gray', 'BlueGray']

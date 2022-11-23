import sqlite3
import sys

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidgetItem, \
    QMainWindow, QVBoxLayout, QPushButton, QTableWidget, QLabel, QButtonGroup
from openingWidget import Ui_Form
from adding_products import Ui_Adding
from main_window import Ui_MainWindow
from PyQt5.QtGui import QPixmap, QFont, QColor


class ItemsError(Exception):
    pass


class Opening(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.textBrowser.setText("""Здравствуйте, дорогой пользователь!
Вы открыли приложение “Подсчёт калорий для ленивых”. 
С его помощью вы сможете проверить пищевую ценность множества разных продуктов. 
Возможно, это поможет вам вести более здоровый образ жизни, не болеть, не толстеть и жить дольше!

        """)
        self.setFixedSize(500, 214)
        self.pushButton.clicked.connect(self.open_main)

    def open_main(self):
        self.second_window = MainApp()
        self.second_window.show()
        self.close()


class MyWidget(QWidget):
    def __init__(self, button_text):
        super(MyWidget, self).__init__()
        self.vLayout = QVBoxLayout(self)
        self.picture_label = QLabel('Изображения нет', self)
        self.picture_label.setAlignment(Qt.AlignCenter)
        self.btn = QPushButton(button_text, self)
        font = QFont()
        font.setPointSize(10)
        self.btn.setFont(font)
        self.vLayout.addWidget(self.picture_label)
        self.vLayout.addWidget(self.btn)


def make_table(self, res, products='chosen'):
    for i, row in enumerate(res):
        if products == 'are':
            row = list(row)
            row.append(100)
        for j, elem in enumerate(row):
            if products == 'searched':
                item = QTableWidgetItem(str(elem))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            else:
                if isinstance(elem, str):
                    item = QTableWidgetItem(str(elem))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                else:
                    item = QTableWidgetItem(str(elem))
            self.table.setItem(i, j, item)
    self.table.resizeColumnsToContents()


class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.con = sqlite3.connect("food_db.db")
        self.make_design()
        # self.selected_items = {}
        self.tables = []
        self.opened_categories = []
        self.index_of_updated_dict = 0
        self.search_btn.clicked.connect(self.search_item)
        self.add_button.clicked.connect(self.add_item)

    def make_design(self):
        self.product_buttons = QButtonGroup(self)
        try:
            query = """SELECT russian_name, name FROM food_categories"""
            categories = self.con.cursor().execute(query).fetchall()
            row = 0
            col = 0
            for category_ru, category_en in categories:
                group = MyWidget(category_ru)
                pixmap = QPixmap('food_images/' + category_en + '.jpg')
                group.picture_label.setPixmap(pixmap.scaled(130, 130, Qt.KeepAspectRatioByExpanding))

                self.product_buttons.addButton(group.btn)
                group.btn.resize(QSize(20, pixmap.width()))
                self.gridLayout_2.addWidget(group, row, col)
                col += 1
                if col == 4:
                    row += 1
                    col = 0
        except sqlite3.OperationalError:
            self.statusbar.showMessage('Ошибка! База данных недоступна')
            self.close()
        self.calc_btn = QPushButton('Посчитать пищевую ценность', self)
        font = QFont()
        font.setPointSize(10)
        self.calc_btn.setFont(font)
        self.verticalLayout.addWidget(self.calc_btn)
        self.calc_btn.clicked.connect(self.calc_nutrition)
        self.product_buttons.buttonClicked.connect(self.show_data)

    def show_data(self, btn):
        if btn.text() in self.opened_categories:
            self.tables[self.opened_categories.index(btn.text())].show()
            self.index_of_updated_dict = self.opened_categories.index(btn.text())
        else:
            self.list_of_products = Table(btn)
            self.list_of_products.show()
            self.opened_categories.append(btn.text())
            self.tables.append(self.list_of_products)
            self.index_of_updated_dict = -1
            self.list_of_products.button.clicked.connect(self.show_chosen)

    def make_dict(self):
        final_dict = {}
        for table in self.tables:
            final_dict.update(table.products_chosen)
        return final_dict

    def show_chosen(self):
        products = self.make_dict()
        self.table.blockSignals(True)
        self.table.setColumnCount(2)
        self.table.setRowCount(len(products))
        self.table.setHorizontalHeaderLabels(['Выбранный продукт', 'Граммы'])
        make_table(self, products.items())
        self.table.blockSignals(False)
        self.table.cellChanged.connect(self.final_dict)

    def final_dict(self, row, col):
        cur = self.con.cursor()
        query = """SELECT russian_name FROM food_categories 
    INNER JOIN all_products
    WHERE all_products.product = ? AND food_categories.id = all_products.category """
        res = cur.execute(query, (self.table.item(row, 0).text(),)).fetchall()
        try:
            self.tables[self.opened_categories.index(*res[0])].products_chosen[self.table.item(row, 0).text()] = \
                int(self.table.item(row, col).text())
        except ValueError:
            self.table.item(row, col).setText('100')

    def calc_nutrition(self):
        cur = self.con.cursor()
        query = """SELECT proteins, fats, carbohydrates, calories FROM all_products
    WHERE product = ?"""
        products = self.make_dict()
        proteins = 0
        fats = 0
        carbs = 0
        calories = 0
        for k, v in products.items():
            nutrition = cur.execute(query, (k,)).fetchall()
            proteins += nutrition[0][0] * (v / 100)
            fats += nutrition[0][1] * (v / 100)
            carbs += nutrition[0][2] * (v / 100)
            calories += nutrition[0][3] * (v / 100)
        self.statusbar.showMessage(f'Белков: {round(proteins, 1)}, жиров: {round(fats, 1)}, '
                                   f'углеводов: {round(carbs, 1)}, калорий: {round(calories, 1)}')

    def add_item(self):
        self.widget_for_adding = AddProduct()
        self.widget_for_adding.show()

    def search_item(self):
        self.new_widget = TableSearch(self.lineEdit.text())
        self.new_widget.show()


class AddProduct(QWidget, Ui_Adding):
    def __init__(self):
        super(AddProduct, self).__init__()
        self.setupUi(self)
        self.con = sqlite3.connect("food_db.db")
        self.add_btn.clicked.connect(self.adding_to_database)

    def adding_to_database(self):
        max_id = 505
        query = """INSERT INTO all_products VALUES(?, ?, ?, ?, ?, 
        (SELECT id FROM food_categories WHERE russian_name = ?), ?)
        """
        res = self.con.cursor().execute('SELECT product FROM all_products WHERE product = ?',
                                        (self.product_name.text().capitalize(),))
        try:
            if tuple(res):
                raise ItemsError
            self.con.cursor().execute(query, (self.product_name.text().capitalize(), float(self.proteins.text()),
                                              float(self.fats.text()), float(self.carbs.text()),
                                              int(self.calories.text()), self.category.text(), max_id + 1))
            self.con.commit()
            max_id += 1
        except ValueError:
            self.label_7.clear()
            self.label_7.setText('Некорректные данные ввода')
        except ItemsError:
            self.label_7.clear()
            self.label_7.setText('Продукт уже есть в базе')
        else:
            self.label_7.clear()
            self.label_7.setText('Продукт добавлен')


class TableSearch(QWidget):
    def __init__(self, name):
        super(TableSearch, self).__init__()
        self.setLayout(QVBoxLayout(self))
        self.setWindowTitle('Поиск продукта')
        self.table = QTableWidget(self)
        self.layout().addWidget(self.table)
        self.label = QLabel(self)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.layout().addWidget(self.label)
        self.con = sqlite3.connect("food_db.db")
        self.select_data(name)
        self.setObjectName('Найти продукты')

    def select_data(self, name):
        query = """SELECT product, proteins, fats, carbohydrates, calories FROM all_products
            WHERE product LIKE ? or product LIKE ? or 
            category LIKE (SELECT ID FROM food_categories WHERE russian_name LIKE ? or russian_name LIKE ?)
                """
        try:
            if not name:
                raise ItemsError
            res = self.con.cursor().execute(query, ('%' + name.capitalize() + '%', '%' + name.lower() + '%',
                                                    '%' + name.capitalize() + '%', '%' + name.lower() + '%')).fetchall()
            if not tuple(res):
                raise ItemsError
            self.table.setColumnCount(5)
            self.table.setRowCount(len(res))
            self.table.setHorizontalHeaderLabels(['продукт', 'белки', 'жиры', 'углеводы', 'калории'])
            make_table(self, res, 'searched')
            self.sizeHint()
        except ItemsError:
            self.label.setText('Продукты не найдены')


class Table(QWidget):
    def __init__(self, btn):
        super(Table, self).__init__()
        self.setWindowTitle('Список продуктов')
        self.setLayout(QVBoxLayout(self))
        self.button = QPushButton('Выбрать', self)
        font = QFont()
        font.setPointSize(10)
        self.button.setFont(font)
        self.table = QTableWidget(self)
        self.layout().addWidget(self.table)
        self.layout().addWidget(self.button)
        self.con = sqlite3.connect("food_db.db")
        self.select_data(btn)
        self.label = QLabel('Введите массу продукта в солбец "Граммы"', self)
        self.label.setFont(font)
        self.layout().addWidget(self.label)
        self.table.cellClicked.connect(self.mark_products)
        self.products_chosen = {}
        self.button.clicked.connect(self.confirm_chosen_products)

    def select_data(self, btn):
        query = """SELECT product from all_products
    WHERE all_products.category = (SELECT id FROM food_categories 
    WHERE russian_name = ?)"""
        res = self.con.cursor().execute(query, (btn.text(),)).fetchall()
        self.table.setColumnCount(1)
        self.table.setRowCount(len(res))
        self.table.insertColumn(1)
        self.table.setHorizontalHeaderLabels(['продукт', 'граммы'])
        make_table(self, res, 'are')
        self.sizeHint()

    def mark_products(self, row, col):
        if self.table.item(row, col).background() == QColor('#9ACEEB'):
            for i in range(self.table.columnCount()):
                self.table.item(row, i).setBackground(QColor('#FFFFFF'))
        else:
            for i in range(self.table.columnCount()):
                self.table.item(row, i).setBackground(QColor('#9ACEEB'))

    def confirm_chosen_products(self):
        for r in range(self.table.rowCount()):
            try:
                if self.table.item(r, 0).background() == QColor('#9ACEEB'):
                    self.products_chosen[self.table.item(r, 0).text()] = int(self.table.item(r, 1).text())
                elif self.table.item(r, 0).background() == QColor('#FFFFFF') and \
                        self.table.item(r, 0).text() in self.products_chosen.keys():
                    self.products_chosen.pop(self.table.item(r, 0).text())
            except ValueError:
                self.label.clear()
                # self.label.setText('Ошибка! Введите число')
                self.table.item(r, 1).setText('100')
        if self.products_chosen:
            self.label.setText('Отлично! Продукты выбраны')


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Opening()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())


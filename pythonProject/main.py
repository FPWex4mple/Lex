import sys
import re
from PyQt6 import QtWidgets, QtGui, QtCore

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Компилятор")
        self.setGeometry(0, 0, 800, 600)
        self.setStyleSheet("background-color: #010101;")

        self.text_field = QtWidgets.QTextEdit(self)
        self.text_field.setGeometry(50, 50, 700, 500)
        self.text_field.setStyleSheet("color: white; background-color: #333333;")

        self.compile_button = QtWidgets.QPushButton("Compile", self)
        self.compile_button.setGeometry(350, 10, 100, 30)
        self.compile_button.clicked.connect(self.compile_code)

        self.shortcut = QtGui.QShortcut(QtGui.QKeySequence('F5'), self)
        self.shortcut.activated.connect(self.compile_code)

        self.token_exprs = [
            (r"[ \n\t]+",            "ws",  "L4"),
            ("#",                    "#",   "L3"),
            ("&",                    "&",   "L6"),
            (";",                    ";",   "L8"),
            ("!",                    "!",   "L5"),
            ("while",                "W",   "L2"),
            (r"[0-9]+",              "d",   "L1"),
            ("{",                    "{",   "L9"),
            (":=",                   ":=",  "L10"),
            ("}",                    "}",   "L11"),
            (r"[_A-Za-z][A-Za-z_]*", "v",   "L7")
        ]

    def compile_code(self):
        code = self.text_field.toPlainText()
        if self.is_valid(code):
            try:
                tokens = self.lex(code)

                # Получаем используемые лексемы
                used_lexemes = [str(token[2]) for token in tokens]

                # Получаем результаты анализатора
                analyzer_results = [str(token[1]) for token in tokens]

                # Формируем сообщение с результатами
                message = 'Код успешно скомпилирован\n'
                message += 'Используемые лексемы: ' + ', '.join(used_lexemes) + '\n'
                message += 'Результат работы лексического анализатора: ' + ', '.join(analyzer_results)
                # Выводим результаты в консоль PyCharm
                print(message)

                self.parse_program(tokens)
                success_dialog = QtWidgets.QMessageBox()
                success_dialog.setIcon(QtWidgets.QMessageBox.Icon.Information)
                success_dialog.setText(message)
                success_dialog.setWindowTitle('Success')
                success_dialog.setStyleSheet(
                    "QLabel{color: black;} QMessageBox{background-color: #FFFFFF;}")
                success_dialog.exec()
            except Exception as e:
                error_dialog = QtWidgets.QMessageBox()
                error_dialog.setIcon(QtWidgets.QMessageBox.Icon.Critical)
                error_dialog.setText('Ошибка: ' + str(e))
                error_dialog.setWindowTitle('Error')
                error_dialog.setStyleSheet(
                    "QLabel{color: black;} QMessageBox{background-color: #FFFFFF;}")
                error_dialog.exec()

    def is_valid(self, code):
        allowed_chars = r"[A-Za-z0-9_#&;!\r\n\t {}:=]*"
        processed_input = re.sub(r"[\r\n\t]", " ", code)
        return re.match("^" + allowed_chars + "$", processed_input) is not None

    def lex(self, characters):
        pos = 0
        tokens = []
        while pos < len(characters):
            match = None
            for pattern, tag, lex in self.token_exprs:
                regex = re.compile("^" + pattern)
                match = regex.match(characters[pos:])
                if match:
                    text = match.group(0)
                    if tag and tag != "ws":  # Игнорируем пробелы и переносы строк
                        tokens.append((text, tag, lex))
                    break
            if not match:
                raise Exception("Illegal character: " + characters[pos])
            pos += len(match.group(0))
        print(tokens)
        return tokens

    def parse_program(self, tokens):
        try:
            self.parse_block(tokens)
            if tokens:
                raise Exception("Неожиданные токены в конце программы")
        except Exception as e:
            raise Exception("Ошибка разбора программы: " + str(e))

    def parse_block(self, tokens):
        try:
            self.parse_operator(tokens)
            if tokens:
                if tokens[0][1] == ";":
                    tokens.pop(0)  # remove ;
                    if tokens and tokens[0][1] == "}":
                        return  # return if end of block
                    if tokens:  # check if there are more tokens
                        self.parse_block(tokens)
                elif tokens[0][1] == "}":
                    return  # return if end of block
                elif tokens[0][1] == "v":
                    self.parse_block(tokens)  # parse next block if it starts with a variable
                else:
                    raise Exception(f"Ожидалось ; или }} или переменная, но найдено {tokens[0][1]}")
        except Exception as e:
            raise Exception("Ошибка разбора блока: " + str(e))

    def parse_operator(self, tokens):
        try:
            if tokens[0][1] == "v":
                tokens.pop(0)  # remove variable
                if tokens[0][1] != ":=":
                    raise Exception(f"Ожидалось :=, но найдено {tokens[0][1]}")
                tokens.pop(0)  # remove :=
                self.parse_expression(tokens)
            elif tokens[0][1] == "W":
                tokens.pop(0)  # remove while
                if tokens[0][1] != "v":
                    raise Exception(f"Ожидалась переменная, но найдено {tokens[0][1]}")
                tokens.pop(0)  # remove variable
                if tokens[0][1] != "{":
                    raise Exception(f"Ожидалось {{, но найдено {tokens[0][1]}")
                tokens.pop(0)  # remove {
                self.parse_block(tokens)
                if tokens[0][1] != "}":
                    raise Exception(f"Ожидалось }}, но найдено {tokens[0][1]}")
                tokens.pop(0)  # remove }
            elif tokens[0][1] in {"#", "!", "&"}:
                self.parse_expression(tokens)
            else:
                raise Exception(f"Ожидался оператор, но найдено {tokens[0][1]}")
        except Exception as e:
            raise Exception("Ошибка разбора оператора: " + str(e))

    def parse_expression(self, tokens):
        try:
            self.parse_factor(tokens)
            while tokens and tokens[0][1] in {"#", "!"}:
                tokens.pop(0)  # remove # or !
                self.parse_factor(tokens)
        except Exception as e:
            raise Exception("Ошибка разбора выражения: " + str(e))

    def parse_factor(self, tokens):
        try:
            self.parse_primary(tokens)
            while tokens and tokens[0][1] == "&":
                tokens.pop(0)  # remove &
                self.parse_primary(tokens)
        except Exception as e:
            raise Exception("Ошибка разбора фактора: " + str(e))

    def parse_primary(self, tokens):
        try:
            if not tokens:
                raise Exception("Ожидался первичный элемент")
            if tokens[0][1] in {"v", "d"}:
                tokens.pop(0)  # remove variable or digit
            elif tokens[0][1] == "!":
                tokens.pop(0)  # remove '!'
                self.parse_expression(tokens)  # parse expression after '!'
            else:
                raise Exception("Ожидался первичный элемент")
        except Exception as e:
            raise Exception("Ошибка разбора первичного элемента: " + str(e))

def test_program():
    # Создаем экземпляр вашей программы
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()

    # Примеры кода для проверки
    test_cases = [
        "v := d;",
        "W v { v := d; }",
        "v := d; W v { v := d; }",
        "v := d; W v { v := d; }; v := d;",
        "v := d; W v { v := d; }; v := d; W v { v := d; };",
        # Добавьте сюда больше тестовых случаев по мере необходимости
    ]

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())


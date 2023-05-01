import os
import subprocess
import sys
import tempfile
import time
import binascii
from PIL import ImageGrab, Image
import clipboard
import keyboard
import pyautogui
import pygetwindow as gw
from lxml import etree
from PyQt5.QtCore import Qt, QTimer, QByteArray
from PyQt5.QtGui import QImage, QPixmap, QKeySequence, QTextDocument
from PyQt5.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame, QHBoxLayout, QAction,
                             QInputDialog, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
                             QSizePolicy, QSplitter, QTableWidget, QTableWidgetItem, QTextBrowser,
                             QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QDialog, QStackedWidget)

from models import Subject, Book, Problem, Solution
from database_functions import create_tables, get_all_data, create_database, create_subject, create_book, add_problem, refresh_table, add_subject, add_book, add_solution, get_subjects, get_books, html_to_plain_text, get_random_problem_with_lowest_solved, mark_solved_correctly
from database_functions import save_time_value, increment_solved_value, save_image
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
import base64
from lxml import html as lxml_html
from io import BytesIO
from datetime import datetime
import random

database_name = 'my_problem_database'
database_path = os.path.abspath('my_problem_database.db')
database_url = f'sqlite:///{database_name}.db'
create_tables(database_url)


engine = create_engine(database_url)
Session = sessionmaker(bind=engine)


def is_base64_image(string):
    try:
        tree = lxml_html.fromstring(string)
        img_element = tree.xpath('//img')
        return True if img_element else False
    except:
        return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Math Problem Reviewer')

        top_layout = QHBoxLayout()

        add_problem_button = QPushButton('Add Problem')
        add_problem_button.clicked.connect(self.add_problem_clicked)
        top_layout.addWidget(add_problem_button)

        browse_button = QPushButton('Browse')
        # Add the appropriate connected function for the Browse button
        browse_button.clicked.connect(self.browse_problems_clicked)
        top_layout.addWidget(browse_button)

        review_settings_button = QPushButton('Review Settings')
        # Add the appropriate connected function for the Review Settings button
        # review_settings_button.clicked.connect(self.review_settings_clicked)
        top_layout.addWidget(review_settings_button)

        start_review_button = QPushButton('Start Review')
        # Set a larger height for the Start Review button
        start_review_button.setFixedHeight(50)
        start_review_button.clicked.connect(self.start_review_clicked)
        # Add the appropriate connected function for the Start Review button
        # start_review_button.clicked.connect(self.start_review_clicked)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(start_review_button)
        main_layout.addStretch()

        self.browse_dialog = None
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def browse_problems_clicked(self):
        self.browse_dialog = BrowseDialog()
        self.browse_dialog.show()

    def add_problem_clicked(self):
        add_problem_dialog = AddProblemDialog()
        result = add_problem_dialog.exec()

        if result == QDialog.Accepted and self.browse_dialog is not None:
            refresh_table(self.browse_dialog, database_name)

    def start_review_clicked(self):
        review_dialog = ReviewDialog()
        review_dialog.exec()


class AddProblemDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add Problem")

        layout = QVBoxLayout()

        # Subject row
        subject_label = QLabel("Subject")
        self.subject_combobox = QComboBox()
        add_subject_button = QPushButton("Add new")
        subject_row = QHBoxLayout()
        subject_row.addWidget(subject_label)
        subject_row.addWidget(self.subject_combobox)
        subject_row.addWidget(add_subject_button)
        layout.addLayout(subject_row)

        # Book row
        book_label = QLabel("Book")
        self.book_combobox = QComboBox()
        add_book_button = QPushButton("Add new")
        book_row = QHBoxLayout()
        book_row.addWidget(book_label)
        book_row.addWidget(self.book_combobox)
        book_row.addWidget(add_book_button)
        layout.addLayout(book_row)

        # Problem input
        self.problem_input = ImageTextEditor()
        layout.addWidget(self.problem_input)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(separator)

        # Solution input
        self.solution_input = ImageTextEditor()
        layout.addWidget(self.solution_input)

        # Add Problem button
        add_problem_button = QPushButton("Add Problem")
        layout.addWidget(add_problem_button)

        self.setLayout(layout)

        self.subject_combobox.currentIndexChanged.connect(self.populate_books)

        add_subject_button.clicked.connect(self.add_new_subject)
        add_book_button.clicked.connect(self.add_new_book)
        add_problem_button.clicked.connect(self.save_problem)
        self.populate_subjects()

    def populate_subjects(self):
        subjects = get_subjects('my_problem_database')
        self.subject_combobox.clear()
        for subject in subjects:
            self.subject_combobox.addItem(subject.name, subject.id)
        if subjects:
            self.populate_books()

    def populate_books(self):
        subject_id = self.subject_combobox.currentData()
        books = get_books('my_problem_database', subject_id)
        self.book_combobox.clear()
        for book in books:
            self.book_combobox.addItem(book.title, book.id)

    def add_new_subject(self):
        text, ok = QInputDialog.getText(self, "New Subject", "Subject Name:")
        if ok and text:
            # Change this line from create_subject to add_subject
            add_subject(text)
            self.populate_subjects()

    def add_new_book(self):
        text, ok = QInputDialog.getText(self, "New Book", "Book Title:")
        if ok and text:
            subject_id = self.subject_combobox.currentData()
            # Change this line from create_book to add_book
            add_book(text, subject_id)
            self.populate_books()

    def get_selected_book_id(self):
        # print(f"heeey bitchhhh {self.book_combobox.currentIndex()}")
        return self.book_combobox.itemData(self.book_combobox.currentIndex())

    def get_selected_subject_id(self):
        return self.subject_combobox.itemData(self.subject_combobox.currentIndex())

    def save_problem(self):
        problem_description = self.problem_input.toHtml()
        solution_description = self.solution_input.toHtml()
        book_id = self.book_combobox.currentData()
        subject_id = self.subject_combobox.currentData()

        if not problem_description or not solution_description:
            QMessageBox.warning(
                self, "Warning", "Please fill in all the fields.")
            return

        image_path = None
        if is_base64_image(problem_description):
            tree = lxml_html.fromstring(problem_description)
            img_element = tree.xpath('//img')[0]
            base64_data = img_element.get('src')
            base64_data = "data:image/png;base64," + base64_data
            image_path = save_image(base64_data)

        add_problem(database_url, problem_description, book_id,
                    solution_description, subject_id, image_path)
        self.close()


class BrowseDialog(QDialog):

    def refresh_table(self):
        refresh_table(self)

    def html_to_plain_text(self, html):
        document = QTextDocument()
        document.setHtml(html)
        return document.toPlainText()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Browse")

        layout = QHBoxLayout()

        # First column (navigation)
        self.navigation_tree = QTreeWidget()
        self.navigation_tree.setColumnCount(1)
        self.navigation_tree.setHeaderLabel("Navigation")

        all_item = QTreeWidgetItem(self.navigation_tree)
        all_item.setText(0, "All")

        subject_item = QTreeWidgetItem(self.navigation_tree)
        subject_item.setText(0, "Subject")
        # Add subject sub-items here
        # e.g. QTreeWidgetItem(subject_item).setText(0, "Subject 1")

        book_item = QTreeWidgetItem(self.navigation_tree)
        book_item.setText(0, "Book")
        # Add book sub-items here
        # e.g. QTreeWidgetItem(book_item).setText(0, "Book 1")

        self.navigation_tree.expandAll()

        # Second column (table)
        self.problems_table = QTableWidget()
        self.problems_table.setColumnCount(6)
        self.problems_table.setHorizontalHeaderLabels(
            ["Problem", "Solution", "Subject", "Book", "Solved", "Time"])
        # Add table items here
        # e.g. self.problems_table.setItem(0, 0, QTableWidgetItem("Problem 1"))

        # Third column (delete button)
        delete_button = QPushButton("Delete")
        delete_button_layout = QVBoxLayout()
        delete_button_layout.addWidget(delete_button)
        delete_button_layout.addStretch()  # Add a stretch to push the button to the top
        delete_button_container = QWidget()
        delete_button_container.setLayout(delete_button_layout)

        # Splitter to organize columns
        splitter = QSplitter()
        splitter.addWidget(self.navigation_tree)
        splitter.addWidget(self.problems_table)
        splitter.addWidget(delete_button_container)
        # Set initial sizes of the splitter
        splitter.setSizes([210, self.width() - 410, 200])
        # Set stretch factor for the second column, so it takes up the remaining space
        splitter.setStretchFactor(1, 1)

        problems_data = get_all_data(database_url)
        # print("Problems data:", problems_data)  # Add this line
        self.problems_table.setRowCount(
            len(problems_data))  # Set the number of rows
        for row, (problem_id, problem_description, solution_description, subject_name, book_title, solved, time) in enumerate(problems_data):
            self.problems_table.setItem(row, 0, QTableWidgetItem(
                self.html_to_plain_text(problem_description)))
            self.problems_table.setItem(row, 1, QTableWidgetItem(
                self.html_to_plain_text(solution_description) if solution_description else ""))
            self.problems_table.setItem(row, 2, QTableWidgetItem(
                subject_name if subject_name else ""))
            self.problems_table.setItem(
                row, 3, QTableWidgetItem(book_title if book_title else ""))
            self.problems_table.setItem(
                row, 4, QTableWidgetItem("Yes" if solved else "No"))
            self.problems_table.setItem(
                row, 5, QTableWidgetItem(str(time) if time else ""))

        layout.addWidget(splitter)

        self.setLayout(layout)

        self.resize(1447, 1019)
        # Set the column widths for the table widget in the second column
        self.navigation_tree.setColumnWidth(0, 200)
        self.problems_table.setColumnWidth(2, 200)


class ReviewDialog(QDialog):

    def show_solution(self):
        self.solution_label.setText(self.solution_description)
        self.show_solution_button.setVisible(False)
        self.correct_button.setVisible(True)
        self.incorrect_button.setVisible(True)
        self.timer.stop()  # Stop the timer

    def correct_clicked(self):
        # Increment the 'solved' value for the current problem
        increment_solved_value(self.current_problem)

        # Save the time value of the timer
        time_value = self.timer_label.text()
        minutes, seconds = map(int, time_value.split(':'))
        total_seconds = minutes * 60 + seconds
        save_time_value(self.current_problem, total_seconds)

        self.current_problem_id = None
        # Reset the Start Review window to show a new problem
        self.reset_review_window()

    def is_html_with_image(self, string):
        try:
            tree = lxml_html.fromstring(string)
            img_element = tree.xpath('//img')
            return True if img_element else False
        except:
            return False

    def incorrect_clicked(self):
        # Reset the Start Review window and show a new problem
        self.reset_review_window()

    def reset_review_window(self):
        self.timer.stop()
        self.timer_label.setText("00:00")
        self.timer.start(1000)
        self.current_problem, problem_description, self.solution_description = get_random_problem_with_lowest_solved(
            database_url)
        self.current_problem_id = self.current_problem

        if self.current_problem.image_path:
            problem_image = QImage(self.current_problem.image_path)
            self.problem_label.setPixmap(QPixmap.fromImage(problem_image))
            self.problem_label.setScaledContents(True)
        else:
            self.problem_label.setText(problem_description)

            self.solution_label.setText("Solution will appear here")
            self.show_solution_button.setVisible(True)
            self.correct_button.setVisible(False)
            self.incorrect_button.setVisible(False)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Start Review")

        main_layout = QVBoxLayout()

        # Timer layout
        timer_layout = QHBoxLayout()
        timer_layout.addStretch()  # Push the timer to the right

        # Timer
        self.timer_label = QLabel("00:00")
        # Set the background to white
        self.timer_label.setStyleSheet("QLabel { background-color : white; }")
        timer_layout.addWidget(self.timer_label)
        timer_container = QWidget()
        timer_container.setLayout(timer_layout)
        main_layout.addWidget(timer_container)

        # Problem section
        problem_section = QVBoxLayout()
        self.problem_label = QLabel("Problem image")
        self.problem_label.setAlignment(Qt.AlignCenter)
        problem_section.addWidget(self.problem_label)
        main_layout.addLayout(problem_section, stretch=1)  # Add stretch factor

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(divider)

        # Solution section
        solution_section = QVBoxLayout()
        self.solution_label = QLabel("Solution will appear here")
        self.solution_label.setWordWrap(True)
        self.solution_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.solution_label.setAlignment(Qt.AlignCenter)
        solution_section.addWidget(self.solution_label)
        # Add stretch factor
        main_layout.addLayout(solution_section, stretch=1)

        # buttons

        buttons_layout = QHBoxLayout()
        self.correct_button = QPushButton("Correct", self)
        self.correct_button.clicked.connect(self.correct_clicked)
        self.correct_button.setVisible(False)
        buttons_layout.addWidget(self.correct_button)

        self.incorrect_button = QPushButton("Incorrect", self)
        self.incorrect_button.clicked.connect(self.incorrect_clicked)
        self.incorrect_button.setVisible(False)
        buttons_layout.addWidget(self.incorrect_button)

        main_layout.addLayout(buttons_layout)
        main_layout.setAlignment(buttons_layout, Qt.AlignCenter)

        # Show Answer button
        self.show_solution_button = QPushButton("Show Answer")
        self.show_solution_button.setSizePolicy(
            QSizePolicy.Maximum, QSizePolicy.Preferred)  # Adjust the size policy
        main_layout.addWidget(self.show_solution_button,
                              alignment=Qt.AlignCenter)  # Center the button

        # Set up the timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        # Update the timer every 1000 milliseconds (1 second)
        self.timer.start(1000)

        # Connect the Show Answer button
        self.show_solution_button.clicked.connect(self.show_solution)

        # Set the initial size of the window
        self.resize(1000, 780)

        self.setLayout(main_layout)

        self.current_problem = get_random_problem_with_lowest_solved(
            database_name)
        if self.current_problem:
            self.current_problem, problem_description, self.solution_description = get_random_problem_with_lowest_solved(
                database_name)
            self.problem_label.setText(problem_description)
        else:
            self.problem_label.setText("No problems available for review.")

    def update_timer(self):
        current_time = self.timer_label.text()
        minutes, seconds = map(int, current_time.split(':'))
        seconds += 1
        if seconds == 60:
            seconds = 0
            minutes += 1
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")


class ImageTextEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Paste):
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()

            if mime_data.hasImage():
                image = QImage(clipboard.image())
                self.textCursor().insertImage(image)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)


def main():
    print(
        f'database_path is {database_path}, and database_URL is {database_url}')
    if not os.path.exists(database_path):
        print(f"Database file does not exist: {database_path}")
    else:
        if not os.access(database_path, os.R_OK | os.W_OK):
            print(
                f"Database file is not readable or writable: {database_path}")
        else:
            print(
                f"Database file exists and is readable and writable: {database_path}")
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

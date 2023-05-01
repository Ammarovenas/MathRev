import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, joinedload, subqueryload
from models import Base, Subject, Book, Problem, Solution
from PyQt5.QtGui import QTextDocument
import random
from datetime import datetime


database_name = 'my_problem_database'
engine = create_engine(f'sqlite:///my_problem_database.db')
Session = sessionmaker(bind=engine)


def html_to_plain_text(html):
    document = QTextDocument()
    document.setHtml(html)
    return document.toPlainText()


def create_tables(database_url):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)


def create_database(database_name):
    engine = create_engine(f'sqlite:///{database_name}.db')
    Base.metadata.create_all(engine)


def get_all_data(database_name):
    engine = create_engine(f'sqlite:///{database_name}.db')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    problems = (
        session.query(
            Problem.id,
            Problem.problem_description,
            Solution.description,
            Subject.name,
            Book.title,
            Problem.solved,
            Problem.time,
        )
        .join(Solution, Solution.problem_id == Problem.id, isouter=True)
        .join(Book, Book.id == Problem.book_id, isouter=True)
        .join(Subject, Subject.id == Problem.subject_id, isouter=True)
        .all()
    )

    return problems


def create_subject(database_name, name):
    engine = create_engine(f'sqlite:///{database_name}.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    new_subject = Subject(name=name)
    session.add(new_subject)
    session.commit()
    session.close()


def create_book(database_name, title, subject_id):
    engine = create_engine(f'sqlite:///{database_name}.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    new_book = Book(title=title, subject_id=subject_id)
    session.add(new_book)
    session.commit()
    session.close()


def add_problem(database_name, problem_description, book_id=None, solution_description=None, subject_id=None, image_path=None):
    engine = create_engine(f'sqlite:///{database_name}.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    book = session.query(Book).filter(
        Book.id == book_id).one_or_none() if book_id else None
    subject = session.query(Subject).filter(
        Subject.id == subject_id).one_or_none() if subject_id else None

    problem = Problem(problem_description=problem_description, book=book, subject=subject,
                      solution=Solution(description=solution_description), image_path=image_path)

    session.add(problem)
    session.commit()
    session.close()


def save_image(base64_data, folder='images'):
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_number = random.randint(1000, 9999)
    file_name = f"{timestamp}_{random_number}.png"
    file_path = os.path.join(folder, file_name)

    data = QByteArray.fromBase64(base64_data.encode())
    image = QImage.fromData(data)
    image.save(file_path)

    return file_path


def refresh_table(dialog_instance, database_name):
    problems_data = create_engine(f'sqlite:///{database_name}.db')
    dialog_instance.problems_table.setRowCount(len(problems_data))
    for row, data in enumerate(problems_data):
        for col, value in enumerate(data):
            table_item = QTableWidgetItem(str(value))
            dialog_instance.problems_table.setItem(row, col, table_item)


def add_subject(name):
    session = Session()
    subject = Subject(name=name)
    session.add(subject)
    session.commit()


def add_book(title, subject_id):
    session = Session()
    book = Book(title=title, subject_id=subject_id)
    session.add(book)
    session.commit()


def add_solution(screenshot_path, problem_id):
    session = Session()
    with open(screenshot_path, 'rb') as f:
        description = f.read()
    solution = Solution(description=description, problem_id=problem_id)
    session.add(solution)
    session.commit()


def get_subjects(database_name):
    engine = create_engine(f'sqlite:///{database_name}.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    subjects = session.query(Subject).all()
    session.close()

    return subjects


def get_books(database_name, subject_id):
    engine = create_engine(f'sqlite:///{database_name}.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    books = session.query(Book).filter(Book.subject_id == subject_id).all()
    session.close()

    return books


def get_random_problem_with_lowest_solved(database_name):
    engine = create_engine(f'sqlite:///{database_name}.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    min_solved = session.query(func.min(Problem.solved)) .scalar()

    eligible_problems = (
        session.query(Problem)
        .options(subqueryload(Problem.solution))
        .filter(Problem.solved == min_solved)
        .all()
    )
    print(eligible_problems)
    random_problem = random.choice(eligible_problems)

    problem_id = random_problem.id
    problem_description = random_problem.problem_description
    solution_description = random_problem.solution.description

    session.commit()
    session.close()

    return problem_id, problem_description, solution_description


def increment_solved_value(problem_id):
    session = Session()
    problem = session.query(Problem).filter(Problem.id == problem_id).one()
    problem.solved += 1
    session.commit()
    session.close()


def save_time_value(problem_id, time_value):
    session = Session()
    problem = session.query(Problem).filter(Problem.id == problem_id).one()
    problem.time = time_value
    session.commit()
    session.close()


def mark_solved_correctly(problem_id, database_name):
    engine = create_engine(f'sqlite:///{database_name}.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    problem = session.query(Problem).filter(Problem.id == problem_id).one()
    problem.solved += 1
    # or use datetime.datetime.now() for a more readable timestamp
    problem.time = time.time()
    session.commit()
    session.close()

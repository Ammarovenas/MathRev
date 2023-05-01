import random
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import models

engine = create_engine('sqlite:///my_problem_database.db')
models.Base.metadata.create_all(engine)

session = Session(engine)

for subject_id in range(1, 11):
    subject = models.Subject(name=f"Subject {subject_id}")
    session.add(subject)

    for book_id in range(1, 3):
        book = models.Book(title=f"Book {book_id} of Subject {subject_id}", subject=subject)
        session.add(book)

        for problem_id in range(1, 6):
            problem = models.Problem(problem_description=f"Problem {problem_id} of Book {book_id} of Subject {subject_id}", book=book, subject=subject)
            solution = models.Solution(description=f"Solution {problem_id} of Book {book_id} of Subject {subject_id}", problem=problem)
            session.add(problem)
            session.add(solution)

session.commit()
session.close()

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    books = relationship('Book', order_by="Book.id", back_populates='subject')  
    problems = relationship('Problem', order_by="Problem.id", back_populates='subject')  

    def __init__(self, name):
        self.name = name

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'))  
    subject = relationship('Subject', back_populates='books')
    problems = relationship('Problem', back_populates='book')

class Problem(Base):
    __tablename__ = 'problems'
    image_path = Column(String, nullable=True)
    id = Column(Integer, primary_key=True)
    problem_description = Column(String, nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=True)
    book = relationship("Book", back_populates="problems")
    subject = relationship("Subject", back_populates="problems")
    solution = relationship('Solution', uselist=False, back_populates='problem')
    solved = Column(Integer, default=0)
    time = Column(Float, nullable=True)

    def __init__(self, problem_description, book_id=None, book=None, subject_id=None, subject=None, solution=None):
        self.problem_description = problem_description
        self.book_id = book_id
        self.book = book
        self.subject_id = subject_id
        self.subject = subject
        self.solution = solution

class Solution(Base):
    __tablename__ = 'solutions'
    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    image_path = Column(String, nullable=True)  # Add this line to include image_path
    problem_id = Column(Integer, ForeignKey('problems.id'))
    problem = relationship('Problem', back_populates='solution')

    def __init__(self, description, problem_id=None, problem=None, image_path=None):
        self.description = description
        self.problem_id = problem_id
        self.problem = problem
        self.image_path = image_path  # Add this line to handle image_path in the constructor

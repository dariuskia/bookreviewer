import csv, os, dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

dotenv.load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# create table
db.execute("CREATE TABLE books (isbn VARCHAR(10) PRIMARY KEY, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year INTEGER NOT NULL)")

# insert data
count = 0
with open("data/books.csv") as f:
    reader = csv.reader(f);
    for row in reader:
        if count == 0:
            count+=1
            continue
        isbn, title, author, year = row
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": int(year)})
db.commit()

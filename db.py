from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

from config import DB_URL

Base = declarative_base()

engine = create_engine(DB_URL, echo=True, future=True)

Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("📦 Tables créées avec succès")
    except Exception as e:
        print(f'❌ Erreur init DB: {e}')


if __name__ == '__main__':
    init_db()
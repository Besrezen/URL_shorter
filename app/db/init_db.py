from app.db.session import Base, engine
from app.models import expired_link, link, project, user


def init() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == '__main__':
    init()

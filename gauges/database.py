from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine, select

from .models import APICall, APIErrorLog

DATABASE_URL = "sqlite:///data/gauges.db"


def get_engine():
    return create_engine(DATABASE_URL)


def create_db_and_tables():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_gauge_data(session: Session, model: type[SQLModel], site_no: str):
    statement = select(model).where(model.site_no == site_no)
    return session.exec(statement).first()


def set_gauge_data(session: Session, model: type[SQLModel], data: SQLModel) -> None:
    session.add(data)
    session.commit()


def log_api_call(session: Session, endpoint: str, data_type: str) -> None:
    now = datetime.utcnow()
    api_call = APICall(endpoint=endpoint, data_type=data_type, timestamp=now)
    session.add(api_call)
    session.commit()


def log_api_error(session: Session, endpoint: str, error_message: str) -> None:
    now = datetime.utcnow()
    api_error = APIErrorLog(endpoint=endpoint, error_message=error_message, timestamp=now)
    session.add(api_error)
    session.commit()


def check_recent_api_call(session: Session, endpoint: str, data_type: str, period_seconds: int) -> bool:
    now = datetime.utcnow()
    period_start = now - timedelta(seconds=period_seconds)
    statement = select(APICall).where(
        APICall.endpoint == endpoint,
        APICall.data_type == data_type,
        APICall.timestamp >= period_start,
    )
    recent_calls = session.exec(statement).all()
    return len(recent_calls) > 0

from datetime import datetime

from sqlmodel import Field, SQLModel


class GaugeDataError(Exception):
    pass


class Gauge(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    site_no: str = Field(index=True)
    station_nm: str
    latitude: float
    longitude: float


class GaugeDetail(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    site_no: str = Field(index=True)
    details: str  # JSON as string
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GaugeStageflow(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    site_no: str = Field(index=True)
    stageflow: str  # JSON as string
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GaugeReach(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    site_no: str = Field(index=True)
    reach: str  # JSON as string
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GaugeHistoricalForecast(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    site_no: str = Field(index=True)
    historical_forecast: str  # JSON as string
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class APICall(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    endpoint: str
    data_type: str
    timestamp: datetime


class APIErrorLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    endpoint: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

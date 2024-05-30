import json
import logging
from datetime import UTC, datetime, timedelta

import requests
from sqlmodel import Session, create_engine

from .api import fetch_data_from_api
from .database import create_db_and_tables, get_gauge_data, set_gauge_data
from .models import (
    Gauge,
    GaugeDataError,
    GaugeDetail,
    GaugeHistoricalForecast,
    GaugeReach,
    GaugeStageflow,
)
from .utils import calculate_bbox

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STALE_TIME = timedelta(minutes=15)


def is_stale(timestamp: datetime) -> bool:
    return datetime.now(tz=UTC) - timestamp > STALE_TIME


def get_gauges_near_location(latitude: float, longitude: float, radius_km: float) -> list[Gauge]:
    url = "https://waterservices.usgs.gov/nwis/site/"
    bbox = calculate_bbox(latitude, longitude, radius_km)
    params = {"format": "rdb", "bBox": bbox, "siteStatus": "active", "siteType": "ST"}
    err_msg = f"No active stream gauges found near ({latitude:.7f}, {longitude:.7f})"
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except (requests.HTTPError, requests.RequestException) as e:
        raise GaugeDataError(err_msg) from e

    gauges = []
    lines = [line for line in response.text.splitlines() if not line.startswith("#")]

    for line in lines[2:]:
        parts = line.split("\t")
        if len(parts) > 2:
            gauge = Gauge(
                site_no=parts[1],
                station_nm=parts[2],
                latitude=float(parts[4]),
                longitude=float(parts[5]),
            )
            gauges.append(gauge)

    if not gauges:
        raise GaugeDataError(err_msg)

    return gauges


def main(latitude: float, longitude: float, radius_km: float) -> None:
    create_db_and_tables()
    engine = create_engine("sqlite:///gauges.db")

    with Session(engine) as session:
        try:
            gauges = get_gauges_near_location(latitude, longitude, radius_km)
        except GaugeDataError as e:
            logger.exception(f"Error fetching gauges: {e.msg}")
            return

        for gauge in gauges:
            logger.info(f"Gauge: {gauge.station_nm} ({gauge.site_no})")

            try:
                details = get_gauge_data(session, GaugeDetail, gauge.site_no)
                if not details or is_stale(details.timestamp):
                    details_data = fetch_data_from_api(
                        f"https://api.water.noaa.gov/nwps/v1/gauges/{gauge.site_no}",
                        session,
                        "details",
                    )
                    details = GaugeDetail(
                        site_no=gauge.site_no,
                        details=json.dumps(details_data),
                        timestamp=datetime.now(tz=UTC),
                    )
                    set_gauge_data(session, GaugeDetail, details)
                logger.info(f"Details retrieved for gauge {gauge.site_no}")

                stageflow = get_gauge_data(session, GaugeStageflow, gauge.site_no)
                if not stageflow or is_stale(stageflow.timestamp):
                    stageflow_data = fetch_data_from_api(
                        f"https://api.water.noaa.gov/nwps/v1/gauges/{gauge.site_no}/stageflow",
                        session,
                        "stageflow",
                    )
                    stageflow = GaugeStageflow(
                        site_no=gauge.site_no,
                        stageflow=json.dumps(stageflow_data),
                        timestamp=datetime.now(tz=UTC),
                    )
                    set_gauge_data(session, GaugeStageflow, stageflow)
                logger.info(f"Stageflow retrieved for gauge {gauge.site_no}")

                reach = get_gauge_data(session, GaugeReach, gauge.site_no)
                if not reach:
                    reach_id = json.loads(details.details)["reachId"]
                    reach_data = fetch_data_from_api(
                        f"https://api.water.noaa.gov/nwps/v1/reaches/{reach_id}",
                        session,
                        "reach",
                    )
                    reach = GaugeReach(
                        site_no=gauge.site_no,
                        reach=json.dumps(reach_data),
                        timestamp=datetime.now(tz=UTC),
                    )
                    set_gauge_data(session, GaugeReach, reach)
                logger.info(f"Reach retrieved for gauge {gauge.site_no}")

                historical_forecast = get_gauge_data(session, GaugeHistoricalForecast, gauge.site_no)
                if not historical_forecast or is_stale(historical_forecast.timestamp):
                    pedts_observed = json.loads(details.details)["pedts"]["observed"]
                    historical_forecast_data = fetch_data_from_api(
                        f"https://api.water.noaa.gov/nwps/v1/products/stageflow/{gauge.site_no}/{pedts_observed}",
                        session,
                        "historical_forecast",
                    )
                    historical_forecast = GaugeHistoricalForecast(
                        site_no=gauge.site_no,
                        historical_forecast=json.dumps(historical_forecast_data),
                        timestamp=datetime.now(tz=UTC),
                    )
                    set_gauge_data(session, GaugeHistoricalForecast, historical_forecast)
                logger.info(f"Historical and Forecast Data retrieved for gauge {gauge.site_no}")
            except GaugeDataError as e:
                logger.exception(f"Error processing gauge {gauge.site_no}: {e}")
                continue

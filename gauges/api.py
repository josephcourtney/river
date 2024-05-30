import requests
from sqlmodel import Session

from .database import check_recent_api_call, log_api_call, log_api_error
from .models import GaugeDataError


def fetch_data_from_api(url: str, session: Session, data_type: str) -> dict:
    headers = {"accept": "application/json"}
    endpoint = url
    if check_recent_api_call(session, endpoint, data_type, period_seconds=900):
        msg = f"Recent data already fetched for {endpoint}"
        raise GaugeDataError(msg)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        log_api_call(session, endpoint, data_type)
    except (requests.HTTPError, requests.RequestException) as e:
        error_message = str(e)
        log_api_error(session, endpoint, error_message)
        msg = f"Failed to fetch data from {url}: {error_message}"
        raise GaugeDataError(msg)
    return response.json()

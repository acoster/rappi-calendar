import zoneinfo
from typing import Annotated, Optional, Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Query, Response

import config
from event_generation import build_calendar

CALENDAR_MEDIA_TYPE = 'text/calendar'
TZ_NAME = 'Europe/Zurich'
TZ = zoneinfo.ZoneInfo(TZ_NAME)

app_config = config.load_config_from_file('data/config.jsonnet')

@asynccontextmanager
async def lifespan(app: FastAPI):
  # Load config during startup rather than at import time.
  app.state.config = config.load_config_from_file("data/config.jsonnet")
  yield


class CalendarResponse(Response):
  media_type = CALENDAR_MEDIA_TYPE


def _resolve_collection_types(types: Optional[Sequence[config.CollectionType]], ) -> Sequence[config.CollectionType]:
  if types is not None:
    return types
  return list(config.CollectionType)


app = FastAPI(lifespan=lifespan)

@app.get('/calendars/waste/{zone}', response_class=CalendarResponse)
async def waste_calendars(zone: config.ZoneId, collection_types: Annotated[
  Optional[Sequence[config.CollectionType]], Query()] = None) -> CalendarResponse:
  """
  Fetches the waste collection calendars for a specified zone and types.

  This endpoint generates a calendar containing waste collection schedules
  for the given zone. If no collection types are specified, calendars for
  all available collection types are included by default. The calendar is
  returned in the iCalendar format.
  """
  app_config: config.Config = app.state.config

  if zone not in app_config.zones:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

  calendar = build_calendar(app_config, zone, _resolve_collection_types(collection_types), TZ)
  return CalendarResponse(content=calendar.to_ical().decode('utf-8'))

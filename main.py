import zoneinfo
from datetime import datetime, date, time
from typing import Annotated, List, Optional
from uuid import uuid5, UUID

from fastapi import FastAPI, HTTPException, status, Query, Response
from icalendar import Calendar, Event

import config

UID_NAMESPACE = UUID("0b6a3d0e-6e19-4c7b-8f58-6d63b9e30a5c")

app = FastAPI()


def stable_event_uuid(zone: config.ZoneId, t: config.CollectionType, event_dt: date) -> str:
  # Use the local date since everything is normalised to all-day.
  name = f"{zone}:{t.value}:{event_dt.isoformat()}"
  return str(uuid5(UID_NAMESPACE, name))


app_config = config.load_config_from_file('data/config.jsonnet')


class CalendarResponse(Response):
  media_type = "text/calendar"


@app.get('/calendars/waste/{zone}', response_class=CalendarResponse)
async def root(zone: config.ZoneId,
               types: Annotated[Optional[List[config.CollectionType]], Query()] = None) -> CalendarResponse:
  zones = app_config.zones
  if zone not in zones:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

  if types is None:
    types = [t for t in config.CollectionType]
  tz = zoneinfo.ZoneInfo('Europe/Zurich')

  event_creation_time = datetime.combine(app_config.start_date, time.min, tzinfo=tz)
  c = Calendar()
  c['prodid'] = '-//Rubbish collection calendar//rapperswil-api.coster.ch//'
  c['version'] = '2.0'
  c['tzid'] = 'Europe/Zurich'

  for t in types:
    type_config = app_config.get_collection_config(t)
    event_title = t.value
    event_description = None

    if type_config is not None:
      event_title = type_config.title
      event_description = type_config.description

    for d in zones[zone].schedules.get(t, []):
      event = Event()
      event['uid'] = stable_event_uuid(zone, t, d.dtstart)
      event['summary'] = event_title
      event.add('dtstamp', event_creation_time)
      event.add('dtstart', d.dtstart)
      event.add('dtend', d.dtend)
      if event_description:
        event['description'] = event_description
      if d.rrule:
        event.add('rrule', d.rrule)
        if d.exceptions:
          event.add('exdate', d.exceptions)
      c.add_component(event)

  return CalendarResponse(content=c.to_ical().decode('utf-8'), media_type="text/calendar")

from datetime import date, datetime, time
from typing import Sequence
from uuid import uuid5, UUID
from zoneinfo import ZoneInfo
from icalendar import Calendar, Event

from config import ZoneId, CollectionType, Config

UID_NAMESPACE = UUID("0b6a3d0e-6e19-4c7b-8f58-6d63b9e30a5c")
PRODID = "-//Rubbish collection calendar//rapperswil-api.coster.ch//"


def _stable_event_uuid(zone: ZoneId, t: CollectionType, event_dt: date) -> str:
  name = f"{zone}:{t.value}:{event_dt.isoformat()}"
  return str(uuid5(UID_NAMESPACE, name))


def build_calendar(app_config: Config, zone: ZoneId, collection_types: Sequence[CollectionType],
                    tz: ZoneInfo) -> Calendar:
  """
  Constructs a calendar object using the provided configurations and schedules. The resulting calendar
  is populated with events derived from the schedule data of specific collection types within a specified
  zone. Each event includes details such as start time, end time, and optional recurrence rules
  or descriptions.

  :param app_config: The configuration object containing application-level settings, including
      collection configurations and zone schedules.
  :type app_config: Config
  :param zone: The identifier for the zone whose schedules will be used to populate the calendar.
  :type zone: ZoneId
  :param collection_types: A sequence of collection types to be used for identifying relevant schedules.
  :type collection_types: Sequence[CollectionType]
  :param tz: The timezone information to apply to event creation timestamps and associated scheduling data.
  :type tz: ZoneInfo
  :return: A calendar object conforming to the iCalendar standard, populated with events based on
      the provided configuration and schedule.
  :rtype: Calendar
  """
  event_creation_time = datetime.combine(app_config.start_date, time.min, tzinfo=tz)

  c =  Calendar()
  c['prodid'] = PRODID
  c['version'] = '2.0'
  c['tzid'] = tz.key

  for t in collection_types:
    type_config = app_config.get_collection_config(t)
    event_title = t.value
    event_description = None

    if type_config is not None:
      event_title = type_config.title
      event_description = type_config.description

    for entry in app_config.zones[zone].schedules.get(t, []):
      event = Event()
      event['uid'] = _stable_event_uuid(zone, t, entry.dtstart)
      event['summary'] = event_title

      event.add('dtstamp', event_creation_time)
      event.add('dtstart', entry.dtstart)
      event.add('dtend', entry.dtend)
      if event_description:
        event['description'] = event_description

      if entry.rrule:
        event.add('rrule', entry.rrule)
        if entry.exceptions:
          event.add('exdate', entry.exceptions)

      c.add_component(event)

  return c

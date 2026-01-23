from datetime import date, datetime
from enum import StrEnum
from typing import List, Union, Mapping, Optional, Annotated

import _jsonnet
from dateutil import rrule
from pydantic import BaseModel, BeforeValidator
from recurrent.event_parser import RecurringEvent

__all__ = ['Zone', 'CollectionType', 'load_config_from_file']


def ensure_string_entry(d: Union[str, date]) -> str:
  if isinstance(d, date):
    return d.isoformat()
  return d


def ensure_string_list(entries: List[Union[str, date]]) -> List[str]:
  return [ensure_string_entry(x) for x in entries]


class CollectionType(StrEnum):
  WASTE = 'waste'
  ORGANIC = 'organic'
  PAPER = 'paper'
  CARDBOARD = 'cardboard'
  METAL = 'metal'


class Schedule(BaseModel):
  dates: Annotated[List[Union[date, str]], BeforeValidator(ensure_string_list)]
  exceptions: Optional[List[Union[date, str]]] = []


class ConfigModel(BaseModel):
  start_date: date
  end_date: date
  zones: Mapping[str, Mapping[CollectionType, Schedule]]


class Zone:
  def __init__(self, schedules: Mapping[CollectionType, Schedule], start_date: date, end_date: date):
    rule_parser = RecurringEvent(now_date=start_date)

    self.dates = {}

    start_dt = datetime(start_date.year, start_date.month, start_date.day)
    end_dt = datetime(end_date.year, end_date.month, end_date.day)

    for collection_type, schedule in schedules.items():
      rule_set = rrule.rruleset()

      exceptions = set()

      for e in (rule_parser.parse(d) for d in schedule.exceptions):
        if rule_parser.is_recurring:
          rule = rrule.rrulestr(e)
          for d in rule.between(start_dt, end_dt, inc=True):
            exceptions.add(datetime(d.year, d.month, d.day))
        else:
          exceptions.add(datetime(e.year, e.month, e.day))

      for entry in (rule_parser.parse(d) for d in schedule.dates):
        if rule_parser.is_recurring:
          rule = rrule.rrulestr(entry)
          rule_set.rrule(rule)
        else:
          rule_set.rdate(datetime(entry.year, entry.month, entry.day))

      self.dates[collection_type] = []
      for event_ts in rule_set.between(start_dt, end_dt, inc=True):
        event_dt = datetime(event_ts.year, event_ts.month, event_ts.day)
        if event_dt not in exceptions:
          self.dates[collection_type].append(event_dt)


def load_config_from_file(path: str) -> Mapping[str, Zone]:
  j = _jsonnet.evaluate_file(path)
  config = ConfigModel.model_validate_json(j)

  zones = {}

  for zone_id, schedules in config.zones.items():
    zones[zone_id] = Zone(schedules,  config.start_date, config.end_date)

  return zones

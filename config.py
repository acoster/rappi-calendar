from datetime import date, datetime
from enum import StrEnum
from typing import List, Union, Mapping, Optional, Annotated

from dateutil import rrule
from pydantic import BaseModel, BeforeValidator
from recurrent.event_parser import RecurringEvent


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
    rule_parser = RecurringEvent()

    self.dates = {}

    start_dt = datetime(start_date.year, start_date.month, start_date.day)
    end_dt = datetime(end_date.year, end_date.month, end_date.day)

    for collection_type, schedule in schedules.items():
      rule_set = rrule.rruleset()

      for e in (rule_parser.parse(d) for d in schedule.exceptions):
        if rule_parser.is_recurring:
          rule = rrule.rrulestr(e)
          for d in rule.between(start_dt, end_dt, inc=True):
            rule_set.exdate(d)
        else:
          rule_set.exdate(datetime(e.year, e.month, e.day))

      for entry in (rule_parser.parse(d) for d in schedule.dates):
        if rule_parser.is_recurring:
          rule = rrule.rrulestr(entry)
          rule_set.rrule(rule)
        else:
          rule_set.rdate(datetime(entry.year, entry.month, entry.day))

      self.dates[collection_type] = [date(d.year, d.month, d.day) for d in rule_set.between(start_dt, end_dt, inc=True)]

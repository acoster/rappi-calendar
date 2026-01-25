import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import List, Union, Mapping, Annotated, Optional, Literal

import _jsonnet
from dateutil import rrule
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from recurrent.event_parser import RecurringEvent


def ensure_string_entry(d: Union[str, date]) -> str:
  if isinstance(d, date):
    return d.isoformat()
  return d


def ensure_string_list(entries: List[Union[str, date]]) -> List[str]:
  return [ensure_string_entry(x) for x in entries]


ZoneId = Literal["1", "2", "3", "4", "5", "6", "7", "8"]


class CollectionType(StrEnum):
  WASTE = 'waste'
  ORGANIC = 'organic'
  PAPER = 'paper'
  CARDBOARD = 'cardboard'
  METAL = 'metal'


class Schedule(BaseModel):
  dates: Annotated[List[str], BeforeValidator(ensure_string_list)]
  exceptions: Annotated[List[str], BeforeValidator(ensure_string_list), Field(default_factory=list)]
  model_config = ConfigDict(extra='forbid', frozen=True)


class CollectionConfig(BaseModel):
  title: str
  description: Optional[str] = ''
  model_config = ConfigDict(extra='forbid', frozen=True)


class ConfigModel(BaseModel):
  start_date: date
  end_date: date
  zones: Mapping[ZoneId, Mapping[CollectionType, Schedule]]
  collection_settings: Mapping[CollectionType, CollectionConfig] = Field(default_factory=dict)
  model_config = ConfigDict(extra='forbid', frozen=True)


@dataclass(frozen=True)
class ScheduleEntry:
  dtstart: date
  dtend: date
  rrule: Optional[str] = None
  exceptions: Optional[List[date]] = None


@dataclass(frozen=True)
class Zone:
  schedules: dict[CollectionType, List[ScheduleEntry]]

  def __init__(self, schedules: Mapping[CollectionType, Schedule], start_date: date, end_date: date):
    rule_parser = RecurringEvent(now_date=start_date)
    object.__setattr__(self, 'schedules', {})

    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    until_str = end_dt.strftime("UNTIL=%Y%m%dT%H%M%S")

    for collection_type, schedule in schedules.items():
      self.schedules[collection_type] = []

      exceptions: set[date] = set()

      # Builds set of exceptions
      for e in (rule_parser.parse(d) for d in schedule.exceptions):
        if rule_parser.is_recurring:
          rule = rrule.rrulestr(e, dtstart=start_dt)
          for d in rule.between(start_dt, end_dt, inc=True):
            exceptions.add(d.date())
        else:
          exceptions.add(e.date())

      for entry in (rule_parser.parse(d) for d in schedule.dates):
        dtstart = start_dt.date() if rule_parser.is_recurring else entry.date()
        entry_rrule = None
        exdates = None

        if rule_parser.is_recurring:
          if 'DTSTART:' in entry:
            match = re.search(r'DTSTART:(\d{8})\n?', entry)
            dtstart = datetime.strptime(match.group(1), '%Y%m%d').date()
            entry = entry[0:match.start()] + entry[match.end():]
          else:
            dtstart = start_dt.date()

          # If the recurrence rule was unconstrained, make it stop at the last day of the calendar's validity.
          if 'UNTIL' not in entry:
            entry = f'{entry};{until_str}'

          entry_rrule = entry

          parsed_rule = rrule.rrulestr(entry, dtstart=dtstart)
          instances = sorted(
            [d.date() for d in parsed_rule.between(datetime.combine(dtstart, time.min), end_dt, inc=True)])

          # Determine which exceptions (bank holidays, etc.) actually cause instances to be skipped.
          actual_exceptions = set(d for d in instances).intersection(exceptions)
          if actual_exceptions:
            exdates = sorted(actual_exceptions)
          entry_rrule = entry_rrule.replace('RRULE:', '').strip()

        s = ScheduleEntry(dtstart=dtstart, dtend=dtstart + timedelta(days=1), rrule=entry_rrule, exceptions=exdates)
        self.schedules[collection_type].append(s)


class Config:
  def __init__(self, raw_config: ConfigModel):
    self._raw_config: ConfigModel = raw_config
    self._zones: dict[ZoneId, Zone] = {}

    for zone_id, zone_config in raw_config.zones.items():
      self._zones[zone_id] = Zone(zone_config, raw_config.start_date, raw_config.end_date)

  def get_collection_config(self, collection_type: CollectionType) -> Optional[CollectionConfig]:
    if collection_type in self._raw_config.collection_settings:
      return self._raw_config.collection_settings[collection_type]
    return None

  @property
  def collection_configs(self) -> Mapping[CollectionType, CollectionConfig]:
    return MappingProxyType(self._raw_config.collection_settings)

  @property
  def zones(self) -> Mapping[ZoneId, Zone]:
    return MappingProxyType(self._zones)

  @property
  def start_date(self) -> date:
    return self._raw_config.start_date

  @property
  def end_date(self) -> date:
    return self._raw_config.end_date


def load_config_from_file(path: str) -> Config:
  j = _jsonnet.evaluate_file(path)
  return Config(ConfigModel.model_validate_json(j))

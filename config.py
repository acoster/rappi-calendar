from datetime import date, datetime, time
from enum import StrEnum
from typing import List, Union, Mapping, Annotated, Optional, Literal

import _jsonnet
from dateutil import rrule
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict
from recurrent.event_parser import RecurringEvent

from dataclasses import dataclass
from types import MappingProxyType

__all__ = ['Zone', 'CollectionType', 'load_config_from_file']


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

class ScheduleEntry:
  rrule: Optional[str] = None
  exceptions: Optional[List[date]] = None
  date: Optional[date] = None

  def __str__(self):
    if self.rrule:
      exdate = ''
      if self.exceptions:
        exdate = f'\nEXDATE:{",".join([d.strftime("%Y%m%d") for d in self.exceptions])}'
      return f'{self.rrule}{exdate}'
    return str(self.date)

@dataclass(frozen=True)
class Zone:
  schedules: dict[CollectionType, List[ScheduleEntry]]

  def __init__(self, schedules: Mapping[CollectionType, Schedule], start_date: date, end_date: date):
    rule_parser = RecurringEvent(now_date=start_date)
    object.__setattr__(self, 'schedules', {})

    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.min)
    dtstart_str = start_dt.strftime("DTSTART:%Y%m%d")

    for collection_type, schedule in schedules.items():
      rule_set = rrule.rruleset()
      self.schedules[collection_type] = []


      exceptions: set[date] = set()

      for e in (rule_parser.parse(d) for d in schedule.exceptions):
        if rule_parser.is_recurring:
          rule = rrule.rrulestr(e, dtstart=start_dt)
          for d in rule.between(start_dt, end_dt, inc=True):
            exceptions.add(d.date())
        else:
          exceptions.add(e)

      for entry in (rule_parser.parse(d) for d in schedule.dates):
        schedule_entry = ScheduleEntry()
        if rule_parser.is_recurring:
          if 'DTSTART' not in entry:
            entry = f'{dtstart_str}\n{entry}'
          schedule_entry.rrule = entry

          parsed_rule = rrule.rrulestr(entry, dtstart=start_dt)
          instances = sorted([d for d in parsed_rule.between(start_dt, end_dt, inc=True)])
          actual_exceptions = set(d for d in instances).intersection(exceptions)
          if actual_exceptions:
            schedule_entry.exceptions = sorted(actual_exceptions)
        else:
          schedule_entry.date = entry.date()
        self.schedules[collection_type].append(schedule_entry)
      print(collection_type.value)
      print([str(x) for x in self.schedules[collection_type]])



class Config:
  def __init__(self, raw_config: ConfigModel):
    self._raw_config : ConfigModel = raw_config
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


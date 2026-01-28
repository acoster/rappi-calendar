from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from icalendar import Calendar, Event
import pytest

from config import Config, ConfigModel, CollectionType, CollectionConfig, Schedule, ScheduleEntry, Zone
from event_generation import build_calendar

def test_build_calendar_empty():
    tz = ZoneInfo("Europe/Zurich")
    start_date = date(2025, 1, 1)
    end_date = date(2025, 12, 31)
    
    config_model = ConfigModel(
        start_date=start_date,
        end_date=end_date,
        zones={"1": {}},
        collection_settings={}
    )
    app_config = Config(config_model)
    
    cal = build_calendar(app_config, "1", [], tz)
    
    assert isinstance(cal, Calendar)
    assert cal['prodid'] == "-//Rubbish collection calendar//rapperswil-api.coster.ch//"
    assert cal['version'] == '2.0'
    assert cal['tzid'] == "Europe/Zurich"
    # Should have no events
    events = [c for c in cal.subcomponents if isinstance(c, Event)]
    assert len(events) == 0

def test_build_calendar_single_event():
    tz = ZoneInfo("Europe/Zurich")
    start_date = date(2025, 1, 1)
    end_date = date(2025, 12, 31)
    event_date = date(2025, 5, 15)
    
    config_model = ConfigModel(
        start_date=start_date,
        end_date=end_date,
        zones={
            "1": {
                CollectionType.WASTE: Schedule(dates=[event_date.isoformat()])
            }
        },
        collection_settings={
            CollectionType.WASTE: CollectionConfig(title="Waste Collection", description="Put it out by 7am")
        }
    )
    app_config = Config(config_model)
    
    cal = build_calendar(app_config, "1", [CollectionType.WASTE], tz)
    
    events = [c for c in cal.subcomponents if isinstance(c, Event)]
    assert len(events) == 1
    event = events[0]
    
    assert event['summary'] == "Waste Collection"
    assert event['description'] == "Put it out by 7am"
    assert event['dtstart'].dt == event_date
    assert event['dtend'].dt == event_date + timedelta(days=1)
    assert 'uid' in event
    
    expected_dtstamp = datetime.combine(start_date, time.min, tzinfo=tz)
    assert event['dtstamp'].dt == expected_dtstamp

def test_build_calendar_multiple_types():
    tz = ZoneInfo("Europe/Zurich")
    start_date = date(2025, 1, 1)
    end_date = date(2025, 12, 31)
    
    config_model = ConfigModel(
        start_date=start_date,
        end_date=end_date,
        zones={
            "1": {
                CollectionType.WASTE: Schedule(dates=["2025-01-10"]),
                CollectionType.PAPER: Schedule(dates=["2025-01-15"])
            }
        },
        collection_settings={
            CollectionType.WASTE: CollectionConfig(title="Waste"),
            CollectionType.PAPER: CollectionConfig(title="Paper")
        }
    )
    app_config = Config(config_model)
    
    cal = build_calendar(app_config, "1", [CollectionType.WASTE, CollectionType.PAPER], tz)
    
    events = [c for c in cal.subcomponents if isinstance(c, Event)]
    assert len(events) == 2
    summaries = sorted([str(e['summary']) for e in events])
    assert summaries == ["Paper", "Waste"]

def test_build_calendar_rrule_and_exceptions():
    tz = ZoneInfo("Europe/Zurich")
    start_date = date(2025, 1, 1)
    end_date = date(2025, 1, 31)
    
    # Weekly on Monday
    config_model = ConfigModel(
        start_date=start_date,
        end_date=end_date,
        zones={
            "1": {
                CollectionType.WASTE: Schedule(
                    dates=["every monday"],
                    exceptions=["2025-01-06"] # First Monday
                )
            }
        },
        collection_settings={}
    )
    app_config = Config(config_model)
    
    cal = build_calendar(app_config, "1", [CollectionType.WASTE], tz)
    
    events = [c for c in cal.subcomponents if isinstance(c, Event)]
    assert len(events) == 1 # There are 4 mondays in Jan 2025: 6, 13, 20, 27.
    # recurrent's "every monday" will be parsed into an RRULE.
    event = events[0]
    assert 'rrule' in event
    assert 'exdate' in event
    
    # Check exdate
    exdates = event['exdate']
    # icalendar's exdate can be a list of vDDDTypes
    if not isinstance(exdates, list):
        exdates = [exdates]
    
    exdate_values = []
    for ex in exdates:
        for d in ex.dts:
            exdate_values.append(d.dt)
            
    assert date(2025, 1, 6) in exdate_values

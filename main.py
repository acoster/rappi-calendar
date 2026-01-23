from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import FastAPI, HTTPException, status, Query, Response
from ics import Calendar, Event

import config

app = FastAPI()

zones = config.load_config_from_file('data/config.jsonnet')


@app.get("/calendars/waste/{zone}")
async def root(zone: str, types: Annotated[Optional[List[config.CollectionType]], Query()] = None):
  if zone not in zones:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

  if types is None:
    types = [t for t in config.CollectionType]

  c = Calendar()
  for t in types:
    for d in zones[zone].dates[t]:
      event = Event(name=t, begin=d, created=datetime.now())
      event.make_all_day()
      c.events.add(event)

  return Response(content=c.serialize(), media_type="text/calendar")

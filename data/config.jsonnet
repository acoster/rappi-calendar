local _bank_holidays = [
  '2026-01-01',  # Neujahr
  '2026-04-03',  # Karfreitag
  '2026-04-06',  # Ostermontag
  '2026-05-14',  # Auffahrt
  '2026-05-24',  # Pfingstmontag
  '2026-12-25',  # Weihnachten
];

local _replacements_for_mondays = [
  '2026-04-07',  # Ersatzdatum für Ostermontag
  '2026-05-25',  # Ersatzdatum für Pfingstmontag
];

local _mondays = {
  dates: ['every Monday after 2026-01-01'] + _replacements_for_mondays,
  exceptions: _bank_holidays
};

local _thursdays = {
  dates: ['every Thursday after 2026-01-01'],
  exceptions: _bank_holidays
};

local EveryFourth(week_day, start_date) = {
  dates: [std.format('every fourth %s starting %s', [week_day, start_date])]
};

{
  start_date: '2026-01-01',
  end_date: '2026-12-31',
  zones: {
    '1': {
      waste: _mondays,
      cardboard: EveryFourth('Wednesday', '2026-01-07'),
      paper: EveryFourth('Wednesday', '2026-01-14')
    },
    '2': {
      waste: _mondays,
      cardboard: EveryFourth('Wednesday', '2026-01-07'),
      paper: EveryFourth('Wednesday', '2026-01-14')
    },
  }
}
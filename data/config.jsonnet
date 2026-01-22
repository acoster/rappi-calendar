local _bank_holidays = [
  '2026-01-01',  // Neujahr
  '2026-04-03',  // Karfreitag
  '2026-04-06',  // Ostermontag
  '2026-05-14',  // Auffahrt
  '2026-05-25',  // Pfingstmontag
  '2026-12-25',  // Weihnachten
];

local _replacements_for_mondays = [
  '2026-04-07',  // Ersatzdatum für Ostermontag
  '2026-05-26',  // Ersatzdatum für Pfingstmontag
];

local _mondays = {
  dates: ['every Monday'] + _replacements_for_mondays,
  exceptions: _bank_holidays,
};

local _thursdays = {
  dates: ['every Thursday'],
  exceptions: _bank_holidays,
};

local EveryFourth(week_day, start_date) = {
  dates: [std.format('every fourth %s starting %s', [week_day, start_date])],
};

local OrganicSchedule(week_day, exceptions=[]) = {
  dates: [
    std.format('every other %s starting the first %s of January 2026 until March 2026', [week_day, week_day]),
    std.format('every %s from march 2026 until december 2026', [week_day]),
    std.format('every other %s starting the first %s of December 2026 until January 2027', [week_day, week_day]),
  ],
  exceptions: exceptions,
};

local _organic_tuesday = OrganicSchedule('Tuesday', _replacements_for_mondays + _bank_holidays);

local SingleDate(date) = {
  dates: [date],
};

{
  start_date: '2026-01-01',
  end_date: '2026-12-31',
  zones: {
    '1': {
      waste: _mondays,
      cardboard: EveryFourth('Wednesday', '2026-01-07'),
      paper: EveryFourth('Wednesday', '2026-01-14'),
      organic: _organic_tuesday,
      metal: SingleDate('2026-12-08'),
    },
    '2': {
      waste: _mondays,
      cardboard: EveryFourth('Wednesday', '2026-01-07'),
      paper: EveryFourth('Wednesday', '2026-01-14'),
      organic: _organic_tuesday,
      metal: SingleDate('2026-12-11'),
    },
    '3': {
      waste: {
        dates: [
          'Every Monday and Thursday',
          '2026-05-15',  // Ersatzdatum für Auffahrt
          '2026-05-26',  // Ersatzdatum für Pfingstmontag
        ],
        exceptions: _bank_holidays,
      },
      cardboard: {
        dates: [
          'Every other Tuesday starting 2026-01-14',
          '2026-09-30',
        ],
        exceptions: ['2026-09-23'],
        organic: _organic_tuesday,
        metal: SingleDate('2026-12-08'),
      },
    },
    '4': {
      waste: _mondays,
      cardboard: EveryFourth('Wednesday', '2026-01-07'),
      organic: _organic_tuesday,
      metal: SingleDate('2026-12-11'),
    },
  },
}

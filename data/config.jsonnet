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

local _replacements_for_thursdays = [
  '2026-05-14',  // Ersatzdatum für Auffahrt
];

local _mondays = {
  dates: ['every Monday starting first Monday of 2026'] + _replacements_for_mondays,
  exceptions: _bank_holidays,
};

local _thursdays = {
  dates: ['every Thursday starting first Thursday of 2026'] + _replacements_for_thursdays,
  exceptions: _bank_holidays,
};

local EveryFourth(week_day, start_date) = {
  dates: [std.format('every fourth %s starting %s', [week_day, start_date])],
};

local OrganicSchedule(week_day, exceptions=[]) = {
  dates: [
    std.format('every other %s starting the first %s of January 2026 until March 2026', [week_day, week_day]),
    std.format('every %s from first %s of march 2026 until december 2026', [week_day, week_day]),
    std.format('every other %s starting the first %s of December 2026 until January 2027', [week_day, week_day]),
  ],
  exceptions: exceptions + _bank_holidays,
};

local _organic_tuesday = OrganicSchedule('Tuesday', _replacements_for_mondays);
local _organic_friday = OrganicSchedule('Friday', _replacements_for_thursdays);

local SingleDate(date) = {
  dates: [date],
};

{
  start_date: '2026-01-01',
  end_date: '2026-12-31',
  zones: {
    local _z = self,

    // Zones 1, 2 and 4 are similar (modulo metal collection and that zone 4 has no paper collection).
    '1': {
      waste: _mondays,
      cardboard: EveryFourth('Wednesday', '2026-01-07'),
      paper: EveryFourth('Wednesday', '2026-01-14'),
      organic: _organic_tuesday,
      metal: SingleDate('2026-12-08'),
    },
    '2': _z['1'] {
      metal: SingleDate('2026-12-11'),
    },
    '4': _z['2'] {
      paper: null,
    },

    '3': {
      waste: {
        dates: ['Every Monday and Thursday starting 2026-01-01'] +
               _replacements_for_mondays + _replacements_for_thursdays,
        exceptions: _bank_holidays,
      },
      cardboard: {
        dates: [
          'Every other Tuesday starting 2026-01-14',
          '2026-09-30',
        ],
        exceptions: ['2026-09-23'],
      },
      organic: _organic_tuesday,
      metal: SingleDate('2026-12-08'),
    },

    '5': {
      waste: _thursdays,
      cardboard: EveryFourth('Wednesday', '2026-01-28'),
      paper: EveryFourth('Wednesday', '2026-01-21'),
      organic: _organic_friday,
      metal: SingleDate('2026-12-11'),
    },
    '6': _z['5'] {
      metal: SingleDate('2026-12-08'),
    },
    '7': {
      waste: _thursdays,
      cardboard: EveryFourth('Wednesday', '2026-01-14'),
      paper: EveryFourth('Wednesday', '2026-01-07'),
      organic: _organic_friday,
      metal: SingleDate('2026-12-08'),
    },
    '8': {
      waste: _thursdays,
      cardboard: EveryFourth('Wednesday', '2026-01-28'),
      paper: EveryFourth('Wednesday', '2026-01-07'),
      organic: _organic_friday,
      metal: SingleDate('2026-12-11'),
    },
  },

  collection_settings: {
    local _t(t) = { title: t },
    waste: _t('General waste'),
    organic: _t('Organic waste'),
    paper: _t('Paper'),
    cardboard: _t('Cardboard'),
    metal: {
      title: 'Metal',
      description: 'All types of metal, without foreign substances. No electric appliances allowed.',
    },
  },
}

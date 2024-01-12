#!/usr/bin/env python3

"""A simple timestamp tool."""

__author__ = 'schrepfer'

import argparse
import calendar
import collections
import datetime
import functools
import io
import logging
import os
import re
import sys
from typing import Optional
import zoneinfo

import termcolor

# pylint: disable=line-too-long

PATTERNS: dict[int, list[str]] = {}

MONTHS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}


LOCALTIME = zoneinfo.ZoneInfo('localtime')
UTC = zoneinfo.ZoneInfo('UTC')


class UTCOffset(datetime.tzinfo):
  """UTCOffset creates a configurable UTC offset with provided hours/minutes."""

  hours: int
  minutes: int

  def __init__(self, hours: int, minutes: int):
    super(datetime.tzinfo, self).__init__()
    self.hours = hours
    self.minutes = minutes

  def utcoffset(self, dt):
    return datetime.timedelta(hours=self.hours, minutes=self.minutes)

  def dst(self, dt):
    return datetime.timedelta(0)

  def tzname(self, dt):
    return '{0}{1:02d}:{2:02d}'.format(
        '-' if self.hours < 0 else '+',
        abs(self.hours), abs(self.minutes))


TZInfo = zoneinfo.ZoneInfo | UTCOffset


class DateTime(object):
  """DateTime provides utilities for generating datetime.datetime objects for provided ZoneInfo."""

  tzinfo: zoneinfo.ZoneInfo

  def __init__(self, tz: str):
    self.tzinfo = zoneinfo.ZoneInfo(tz) if tz else LOCALTIME

  @functools.cache
  def now(self) -> datetime.datetime:
    return datetime.datetime.now(tz=self.tzinfo)

  def fromtimestamp(self, timestamp) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(timestamp, tz=self.tzinfo)

  def datetime(self, year: int, month: int, day: int,
               hour: int = 0, minute: int = 0, second: int = 0, microsecond: int = 0,
               tzinfo: Optional[TZInfo] = None) -> datetime.datetime:
    if not tzinfo:
      tzinfo = self.tzinfo
    return datetime.datetime(
        year, month, day,
        hour=hour, minute=minute, second=second,
        microsecond=microsecond, tzinfo=tzinfo)


def register(pattern: str, priority: int = 0):
  """Decorator for registering parsers."""
  def wrapper(function):
    section = PATTERNS.setdefault(priority, [])
    section.append((pattern, function))
    return function
  return wrapper


@register(r'^(?P<timestamp>-?\d+(\.\d+)?)$')
def time_parser(dt: DateTime, timestamp: str = '0') -> Optional[datetime.datetime]:
  ts = float(timestamp)
  if ts >= 1e12:
    return None
  return dt.fromtimestamp(ts)


@register(r'^0x(?P<timestamp>-?[0-9a-f]+)$')
def hex_time_parser(dt: DateTime, timestamp: str = '0') -> Optional[datetime.datetime]:
  ts = int(timestamp, 16)
  return dt.fromtimestamp(ts)


@register(r'^(?P<timestamp>-?\d{12,})$', priority=-5)
def time_msec_parser(dt: DateTime, timestamp: str = '0') -> Optional[datetime.datetime]:
  ts = float(timestamp)
  if ts >= 1e15:
    return None
  return dt.fromtimestamp(ts / 1e3)


@register(r'^(?P<timestamp>-?\d{15,})$', priority=-10)
def time_usec_parser(dt: DateTime, timestamp: str = '0') -> Optional[datetime.datetime]:
  ts = float(timestamp)
  return dt.fromtimestamp(ts / 1e6)


@register(r'^(?P<timestamp>-?\d{18,})$', priority=-15)
def time_nsec_parser(dt: DateTime, timestamp: str = '0') -> Optional[datetime.datetime]:
  ts = float(timestamp)
  return dt.fromtimestamp(ts / 1e9)


@register(r'^0x(?P<timestamp>-?[0-9a-f]{10,})$', priority=-10)
def hex_time_usec_parser(dt: DateTime, timestamp: str = '0') -> Optional[datetime.datetime]:
  ts = int(timestamp, 16)
  return dt.fromtimestamp(ts / 1e6)


def datetime_parser(dt: DateTime, year: int = 0, month: int = 0, day: int = 0,
                    hour: int = 0, minute: int = 0, second: float = 0.0,
                    offset_hours: int = 0, offset_minutes: int = 0,
                    z: bool = False) -> Optional[datetime.datetime]:
# if year < 1900:
#   return None
  if month < 1 or month > 12:
    return None
  if day < 1 or day > 31:
    return None
  if hour > 23 or minute > 59 or second > 59:
    return None
  microsecond = int(1e6 * (second % 1))
  isecond = int(second)
  tzinfo: Optional[TZInfo] = None
  if offset_hours or offset_minutes:
    tzinfo = UTCOffset(offset_hours, offset_minutes)
  elif z:
    tzinfo = UTC
  try:
    return dt.datetime(
        year, month, day,
        hour=hour,
        minute=minute,
        second=isecond,
        microsecond=microsecond,
        tzinfo=tzinfo)
  except ValueError:
    return None


@register(
    r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2}) '
    r'(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}(\.\d+)?)$', priority=-10)
@register(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})$')
@register(r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$')
@register(
    r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}) '
    r'(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}(\.\d+)?)$', priority=-10)
@register(r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$')
@register(
    r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})-'
    r'(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}(\.\d+)?)$', priority=-10)
@register(r'^(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})$', priority=-10)
@register(
    r'^(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})T'
    r'(?P<hour>\d{2})(?P<minute>\d{2})$')
@register(
    r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T'
    r'(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}(\.\d+)?)(?P<z>Z?)$')
@register(
    r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T'
    r'(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}(\.\d+)?)'
    r'(?P<offset>[+-](?P<offset_hours>\d{2}):(?P<offset_minutes>\d{2}))$')
def yyyymmdd_hhmmss_parser(dt: DateTime, year: str = '0', month: str = '0', day: str = '0',
                           hour: str = '0', minute: str = '0', second: str = '0',
                           offset: str = '', offset_hours: str = '0', offset_minutes: str = '0',
                           z: Optional[str] = None) -> Optional[datetime.datetime]:
  sign = 1
  if offset.startswith('-'):
    sign = -1

  return datetime_parser(
      dt,
      year=int(year),
      month=int(month),
      day=int(day),
      hour=int(hour),
      minute=int(minute),
      second=float(second),
      offset_hours=int(offset_hours) * sign,
      offset_minutes=int(offset_minutes) * sign,
      z=bool(z),
  )


@register(
    r'^(?P<month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|June?|July?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?) '
    r'(?P<day>\d+)(?: (?P<year>\d+))?$')
def english_parser(dt: DateTime, year: str = '0', month: str = '0', day: str = '0') -> Optional[datetime.datetime]:
  return datetime_parser(
      dt,
      year=int(year) if year else dt.now().year,
      month=MONTHS.get(month[:3], 0),
      day=int(day),
  )


@register(
    r'^(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat) '
    r'(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) +'
    r'(?P<day>\d+) (?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}) '
    r'(?:[A-Z0-9]+ )?'
    r'(?P<year>\d{4})$')
def ctime_parser(dt: DateTime, year: str = '0', month: str = '0', day: str = '0', hour: str = '0', minute: str = '0', second: str = '0') -> Optional[datetime.datetime]:
  return datetime_parser(
      dt,
      year=int(year),
      month=MONTHS.get(month[:3], 0),
      day=int(day),
      hour=int(hour),
      minute=int(minute),
      second=int(second),
  )


@register(r'^(?P<month>[01]?[0-9])[-/](?P<day>[0-3]?[0-9])$')
def month_day_parser(dt: DateTime, month: str = '0', day: str = '0') -> Optional[datetime.datetime]:
  return datetime_parser(
      dt,
      year=dt.now().year,
      month=int(month),
      day=int(day),
  )


@register(r'^(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}(\.\d+)?)$')
def hhmmss_parser(dt: DateTime, hour: str = '0', minute: str = '0', second: str = '0') -> Optional[datetime.datetime]:
  now = dt.now()
  return yyyymmdd_hhmmss_parser(
      year=now.year,
      month=now.month,
      day=now.day,
      hour=hour,
      minute=minute,
      second=second,
      dt=dt,
  )


@register(r'^(?P<count>\d+)(?P<unit>[dsmhw]) ?ago$')
@register(r'^(?P<count>\d+)(?P<unit>d)ays?ago$')
def delta_parser(dt: DateTime, count: str = '0', unit: str = '') -> Optional[datetime.datetime]:
  n = int(count)
  kwargs = {}
  if unit == 'd':
    kwargs['days'] = n
  elif unit == 's':
    kwargs['seconds'] = n
  elif unit == 'm':
    kwargs['minutes'] = n
  elif unit == 'h':
    kwargs['hours'] = n
  elif unit == 'w':
    kwargs['weeks'] = n
  timedelta = datetime.timedelta(**kwargs)
  return dt.now() - timedelta


@register(r'^in(?P<count>\d+)(?P<unit>[dsmhw]) ?$')
@register(r'^in(?P<count>\d+)(?P<unit>d)ays?$')
def future_delta_parser(dt: DateTime, count: str = '0', unit: str = '') -> Optional[datetime.datetime]:
  n = -int(count)
  kwargs = {}
  if unit == 'd':
    kwargs['days'] = n
  elif unit == 's':
    kwargs['seconds'] = n
  elif unit == 'm':
    kwargs['minutes'] = n
  elif unit == 'h':
    kwargs['hours'] = n
  elif unit == 'w':
    kwargs['weeks'] = n
  timedelta = datetime.timedelta(**kwargs)
  return dt.now() - timedelta


def unknown_parser(dt: DateTime) -> Optional[datetime.datetime]:
  return dt.fromtimestamp(0)


def uncolored(text: str, unused_groups) -> str:
  return text


def colored(text: str, groups) -> str:
  i = 0
  buf = io.StringIO()
  for m in re.finditer(
      r'\b(?P<digit>(0x[0-9a-f]+)|\d+)\b'
      r'|(?P<word>\w+)'
      r'|(?P<symbol>[!-/:-@\[-`]+)'
      r'|(?P<space>\s+)'
      r'|(?P<other>\S+)', text):
    buf.write(text[i:m.start()])
    for k, v in m.groupdict().items():
      if not v:
        continue
      if k not in groups:
        k = 'default'
      if k in groups:
        buf.write(termcolor.colored(m.group(0), **groups[k]))
      else:
        buf.write(m.group(0))
    i = m.end()
  buf.write(text[i:])
  return buf.getvalue()


VALUE_COLORS = {
    'digit': {'color': 'red'},
    'day': {'color': 'yellow', 'attrs': ['bold']},
    'month': {'color': 'yellow', 'attrs': ['bold']},
    'zone': {'color': 'yellow', 'attrs': ['bold']},
    'word': {'color': 'red', 'attrs': ['bold']},
    'symbol': {'color': 'yellow', 'attrs': ['bold']},
}


OTHER_COLORS = {
    'default': {'color': 'blue', 'attrs': ['bold']},
    'symbol': {'color': 'green', 'attrs': ['bold']},
}


def display_timestamp(
    now: datetime.datetime,
    base: datetime.datetime,
    text: str,
    fmt: str,
    timezone: str,
    color: bool = False) -> None:
  buf = io.StringIO()
  tzinfo = zoneinfo.ZoneInfo(timezone) if timezone else LOCALTIME
  timestamp = base.astimezone(tzinfo)
  delta = timestamp - now
  timetuple = timestamp.timetuple()
  time_sec = calendar.timegm(timetuple)
  time_usec = time_sec * 1e6 + timestamp.microsecond
  c = colored if color else uncolored

  left_dashes = '-' * ((80 - len(text) - 2) // 2)
  right_dashes = '-' * (80 - len(text) - 2 - len(left_dashes))

  buf.write(c(left_dashes, OTHER_COLORS))
  buf.write(' ' + c(text, OTHER_COLORS) + ' ')
  buf.write(c(right_dashes, OTHER_COLORS))
  buf.write('\n')
  buf.write(c('%23s' % 'base(fmt): ', OTHER_COLORS))
  buf.write(c('%56s' % base.strftime(fmt), VALUE_COLORS))
  buf.write('\n')
  buf.write(c('%23s' % 'Seconds since epoch: ', OTHER_COLORS))
  buf.write(c('%56f' % (time_usec / 1e6), VALUE_COLORS))
  buf.write('\n')
  buf.write(c('%23s' % 'uSeconds since epoch: ', OTHER_COLORS))
  buf.write(c('%56d' % time_usec, VALUE_COLORS))
  buf.write('\n')
  buf.write(c('%23s' % 'rfc3339: ', OTHER_COLORS))
  buf.write(c('%56s' % timestamp.isoformat(), VALUE_COLORS))
  buf.write('\n')
  buf.write(c('%23s' % 'ctime(): ', OTHER_COLORS))
  buf.write(c('%56s' % timestamp.ctime(), VALUE_COLORS))
  buf.write('\n')
  buf.write(c('%23s' % 'strftime(fmt): ', OTHER_COLORS))
  buf.write(c('%56s' % timestamp.strftime(fmt), VALUE_COLORS))
  buf.write('\n')

  if delta:
    buf.write(c('%23s' % 'Delta: ', OTHER_COLORS))
    buf.write(c('%56s' % ((
        '+' if delta.days > 0 else '-') + str(abs(delta))), VALUE_COLORS))
    buf.write('\n')

  buf.write(c('%23s' % 'Day of Year (Week): ', OTHER_COLORS))
  buf.write(c('%56s' % ('%d (%d)' % (
      timetuple.tm_yday, timetuple.tm_wday)), VALUE_COLORS))
  buf.write('\n')

  print(buf.getvalue())


def define_flags() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__)
  # See: http://docs.python.org/3/library/argparse.html
  parser.add_argument(
      '-v', '--verbosity',
      action='store',
      default=20,
      metavar='LEVEL',
      type=int,
      help='the logging verbosity')
  parser.add_argument(
      '-a', '--all',
      action='store_true',
      default=False,
      help='execute all registered parsers')
  parser.add_argument(
      '-V', '--version',
      action='version',
      version='%(prog)s version 0.1')
  parser.add_argument(
      '-f', '--fmt',
      action='store',
      default='%Y-%m-%d %H:%M:%S %Z',
      metavar='FORMAT',
      type=str,
      help='date format')
  parser.add_argument(
      '-s', '--src',
      action='store',
      default=None,
      metavar='TIMEZONE',
      help='e.g. UTC, US/Pacific, Europe/Amsterdam, UTC, etc.')
  parser.add_argument(
      '-d', '--dest',
      action='store',
      default='US/Pacific',
      metavar='TIMEZONE',
      help='e.g. UTC, US/Pacific, Europe/Amsterdam, UTC, etc.')
  parser.add_argument(
      '-c', '--color',
      action='store_true',
      default=True,
      help='display colored output')
  parser.add_argument(
      '--no-color',
      dest='color',
      action='store_false')
  parser.add_argument(
      '-n', '--sorted',
      action='store_true',
      default=False,
      help='sort the output chronologically')
  parser.add_argument(
      '-x', '--hide-now',
      action='store_false',
      dest='show_now',
      default=True,
      help='suppress the display of now')
  parser.add_argument(
      'query',
      nargs='*',
      type=str,
      help='timestamp queries',
      metavar='QUERY')

  args = parser.parse_args()
  check_flags(parser, args)
  return args


def check_flags(unused_parser: argparse.ArgumentParser, unused_args: argparse.Namespace) -> None:
  # See: http://docs.python.org/2/library/argparse.html#exiting-methods
  return


Timestamp = collections.namedtuple('Timestamp', ['datetime', 'text', 'index'])


def append_parser(timestamps: list[Timestamp], timestamp: datetime.datetime, parser, i: int, query: str):
  fmt = '({0}) {1}({2})'.format(i, parser.__name__, query)
  timestamps.append(Timestamp(timestamp, fmt, i))


def main(args):
  dt = DateTime(args.src)
  timestamps = []
  for i, query in enumerate(args.query):
    query = query.strip()
    found = False
    for _, patterns in sorted(PATTERNS.items()):
      for pattern, parser in patterns:
        if m := re.match(pattern, query):
          timestamp = parser(dt=dt, **m.groupdict())
          if not timestamp:
            continue

          append_parser(timestamps, timestamp, parser, i, query)
          found = True
          break

      if found and not args.all:
        break

    if not found:
      append_parser(timestamps, unknown_parser(dt=dt), unknown_parser, i, query)

  now = dt.now()
  if timestamps:
    for timestamp in sorted(timestamps, key=lambda x: x.datetime if args.sorted else x.index):
      display_timestamp(
          now,
          timestamp.datetime,
          timestamp.text,
          args.fmt,
          args.dest,
          color=args.color)
      print()

  if args.show_now:
    display_timestamp(
        now,
        now,
        'datetime.datetime.now()',
        args.fmt,
        args.dest,
        color=args.color)

  return os.EX_OK


if __name__ == '__main__':
  a = define_flags()
  logging.basicConfig(
      level=a.verbosity,
      datefmt='%Y/%m/%d %H:%M:%S',
      format='[%(asctime)s] %(levelname)s: %(message)s')
  sys.exit(main(a))

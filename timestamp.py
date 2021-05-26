#!/usr/bin/env python3

"""A simple timestamp tool."""

__author__ = 'schrepfer'

import argparse
import calendar
import collections
import datetime
import io
import locale
import logging
import os
import re
import sys
import time

import pytz
import termcolor

PATTERNS = {}

MONTHS = {
  'Jan': 1,
  'Feb': 2,
  'Mar': 3,
  'Apr': 4,
  'May': 5,
  'Jun': 6,
  'Jul': 7,
  'Aug': 8,
  'Sep': 9,
  'Oct': 10,
  'Nov': 11,
  'Dec': 12,
  }


def Local():
  with open('/etc/localtime', 'rb') as f:
    return pytz.tzfile.build_tzinfo('/etc/localtime', f)


Local = Local()
UTC = pytz.timezone('UTC')


def register(pattern, priority=0):
  """Decorator for registering parsers."""
  def wrapper(function):
    section = PATTERNS.setdefault(priority, [])
    section.append((pattern, function))
    return function
  return wrapper


@register(r'^(?P<timestamp>-?\d+(\.\d+)?)$')
def timeParser(timestamp=0, dt=None):
  timestamp = float(timestamp)
  if timestamp >= 1e12:
    return None
  return dt.fromtimestamp(timestamp)


@register(r'^0x(?P<timestamp>-?[0-9a-f]+)$')
def hexTimeParser(timestamp='0', dt=None):
  timestamp = int(timestamp, 16)
  return dt.fromtimestamp(timestamp)


@register(r'^(?P<timestamp>-?\d{12,})$', priority=-5)
def timeMsecParser(timestamp=0, dt=None):
  timestamp = float(timestamp)
  if timestamp >= 1e15:
    return None
  return dt.fromtimestamp(timestamp / 1e3)


@register(r'^(?P<timestamp>-?\d{15,})$', priority=-10)
def timeUsecParser(timestamp=0, dt=None):
  timestamp = float(timestamp)
  return dt.fromtimestamp(timestamp / 1e6)


@register(r'^(?P<timestamp>-?\d{18,})$', priority=-15)
def timeNsecParser(timestamp=0, dt=None):
  timestamp = float(timestamp)
  return dt.fromtimestamp(timestamp / 1e9)


@register(r'^0x(?P<timestamp>-?[0-9a-f]{10,})$', priority=-10)
def hexTimeUsecParser(timestamp='0', dt=None):
  timestamp = int(timestamp, 16)
  return dt.fromtimestamp(timestamp / 1e6)


class utcOffset(datetime.tzinfo):

  def __init__(self, hours, minutes):
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
def yyyyMmDdHhMmSsParser(year=0, month=0, day=0, hour=0, minute=0, second=0, z=None,
                         offset=None, offset_hours=0, offset_minutes=0, dt=None):
  year = int(year)
  month = int(month)
  day = int(day)
  hour = int(hour)
  minute = int(minute)
  second = float(second)
# if year < 1900:
#   return None
  if month < 1 or month > 12:
    return None
  if day < 1 or day > 31:
    return None
  if hour > 23 or minute > 59 or second > 59:
    return None
  microsecond = int(1e6 * (second % 1))
  second = int(second)
  tzinfo = UTC if z else None
  if offset:
    sign = (-1 if offset.startswith('-') else 1)
    offset_hours = int(offset_hours) * sign
    offset_minutes = int(offset_minutes) * sign
    tzinfo = utcOffset(offset_hours, offset_minutes)
  try:
    return dt.datetime(
        year, month, day,
        hour=hour,
        minute=minute,
        second=second,
        microsecond=microsecond,
        tzinfo=tzinfo)
  except ValueError:
    return None


@register(
  r'^(?P<month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|June?|July?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?) '
  r'(?P<day>\d+)(?: (?P<year>\d+))?$')
def englishParser(year=0, month=0, day=0, dt=None):
  now = dt.now()
  year = int(year) if year else now.year
  month = MONTHS.get(month[:3], 0)
  day = int(day)
  return yyyyMmDdHhMmSsParser(year=year, month=month, day=day, dt=dt)


@register(
  r'^(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat) '
  r'(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) +'
  r'(?P<day>\d+) (?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}) '
  r'(?:[A-Z0-9]+ )?'
  r'(?P<year>\d{4})$')
def ctimeParser(year=0, month=0, day=0, hour=0, minute=0, second=0, dt=None):
  year = int(year)
  month = MONTHS.get(month[:3], 0)
  day = int(day)
  hour = int(hour)
  minute = int(minute)
  second = int(second)
  return yyyyMmDdHhMmSsParser(
      year=year,
      month=month,
      day=day,
      hour=hour,
      minute=minute,
      second=second,
      dt=dt)


@register(r'^(?P<month>[01]?[0-9])[-/](?P<day>[0-3]?[0-9])$')
def monthDayParser(month=0, day=0, dt=None):
  now = dt.now()
  return yyyyMmDdHhMmSsParser(
      year=now.year,
      month=month,
      day=day,
      dt=dt)


@register(r'^(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}(\.\d+)?)$')
def hhMmSsParser(hour=0, minute=0, second=0, dt=None):
  now = dt.now()
  return yyyyMmDdHhMmSsParser(
      year=now.year,
      month=now.month,
      day=now.day,
      hour=hour,
      minute=minute,
      second=second,
      dt=dt)


@register(r'^(?P<count>\d+)(?P<unit>[dsmhw]) ?ago$')
@register(r'^(?P<count>\d+)(?P<unit>d)ays?ago$')
def deltaParser(count, unit, dt=None):
  now = dt.now()
  count = int(count)
  kwargs = {}
  if unit == 'd':
    kwargs['days'] = count
  elif unit == 's':
    kwargs['seconds'] = count
  elif unit == 'm':
    kwargs['minutes'] = count
  elif unit == 'h':
    kwargs['hours'] = count
  elif unit == 'w':
    kwargs['weeks'] = count
  timedelta = datetime.timedelta(**kwargs)
  return now - timedelta


@register(r'^in(?P<count>\d+)(?P<unit>[dsmhw]) ?$')
@register(r'^in(?P<count>\d+)(?P<unit>d)ays?$')
def futureDeltaParser(count, unit, dt=None):
  now = dt.now()
  count = -int(count)
  kwargs = {}
  if unit == 'd':
    kwargs['days'] = count
  elif unit == 's':
    kwargs['seconds'] = count
  elif unit == 'm':
    kwargs['minutes'] = count
  elif unit == 'h':
    kwargs['hours'] = count
  elif unit == 'w':
    kwargs['weeks'] = count
  timedelta = datetime.timedelta(**kwargs)
  return now - timedelta


def unknownParser(dt=None):
  return dt.fromtimestamp(0)


def uncolored(text, *args, **kwargs):
  return text


def colored(text, groups):
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


def displayTimestamp(now, base, text, fmt, timezone, color=False):
  buf = io.StringIO()
  tzinfo = pytz.timezone(timezone) if timezone else Local
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


def defineFlags():
  parser = argparse.ArgumentParser(description=__doc__)
  # See: http://docs.python.org/2/library/argparse.html
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
      'query',
      nargs='*',
      type=str,
      help='timestamp queries',
      metavar='QUERY')

  args = parser.parse_args()
  checkFlags(parser, args)
  return args


def checkFlags(parser, args):
  # See: http://docs.python.org/2/library/argparse.html#exiting-methods
  return


class dateTime(object):
  def __init__(self, tz):
    self.tzinfo = pytz.timezone(tz) if tz else Local
    self._now = None

  def fromtimestamp(self, timestamp):
    return datetime.datetime.fromtimestamp(timestamp, tz=self.tzinfo)

  def datetime(self, year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None):
    if not tzinfo:
      tzinfo = self.tzinfo
    return datetime.datetime(
        year, month, day,
        hour=hour, minute=minute, second=second,
        microsecond=microsecond, tzinfo=tzinfo)

  def now(self):
    # Cache this. Is this what we want to do? Might be weird.
    if not self._now:
      self._now = datetime.datetime.now(tz=self.tzinfo)
    return self._now

Timestamp = collections.namedtuple('Timestamp', ['datetime', 'text', 'index'])

def appendParser(timestamps, timestamp, parser, i, query):
  fmt = '({0}) {1}({2})'.format(i, parser.__name__, query)
  timestamps.append(Timestamp(timestamp, fmt, i))


def main(args):
  dt = dateTime(args.src)
  timestamps = []
  for i, query in enumerate(args.query):
    query = query.strip()
    found = False
    for priority, patterns in sorted(PATTERNS.items()):
      for pattern, parser in patterns:
        match = re.match(pattern, query)
        if match:
          timestamp = parser(dt=dt, **match.groupdict())
          if not timestamp:
            continue

          appendParser(timestamps, timestamp, parser, i, query)
          found = True
          break

      if found and not args.all:
        break

    if not found:
      appendParser(timestamps, unknownParser(dt=dt), unknownParser, i, query)

  now = dt.now()
  if timestamps:
    for timestamp in sorted(timestamps, key=lambda x: x.datetime if args.sorted else x.index):
      displayTimestamp(
          now,
          timestamp.datetime,
          timestamp.text,
          args.fmt,
          args.dest,
          color=args.color)
      print

  displayTimestamp(now, now, 'datetime.datetime.now()',
                   args.fmt, args.dest, color=args.color)

  return os.EX_OK


if __name__ == '__main__':
  args = defineFlags()
  logging.basicConfig(
      level=args.verbosity,
      datefmt='%Y/%m/%d %H:%M:%S',
      format='[%(asctime)s] %(levelname)s: %(message)s')
  sys.exit(main(args))

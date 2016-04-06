from __future__ import print_function

from collections import OrderedDict
from datetime import datetime as dt
from datetime import timedelta

import calendar
import os
import sys

import re
from termcolor import colored


LOG_FILE = os.path.expanduser('~/timelog.txt')
DATETIME_FORMAT = '%Y-%m-%d %H:%M'
DATE_FORMAT = '%Y-%m-%d'
DATE_FORMAT_FOR_STATS = '%a %d %b %Y'
# length of date string
DATE_LEN = 10
# length of datetime string
DATETIME_LEN = 16


def write_to_log_file(message):
    log_message = form_log_message(message)
    if not os.path.exists(os.path.dirname(LOG_FILE)):
        os.makedirs(os.path.dirname(LOG_FILE))
    with open(LOG_FILE, 'a') as fp:
        fp.write(log_message)


def form_log_message(message):
    time_str = dt.now().strftime(DATETIME_FORMAT)
    log_message = ' '.join((time_str, message))
    if is_another_day():
        return '\n' + log_message + '\n'
    else:
        return log_message + '\n'


def is_another_day():
    """
    Checks if new message is written in the next day,
    than the last log entry.

    date - message date
    """
    try:
        f = open(LOG_FILE, 'r')
        last_line = f.readlines()[-1]
    except (IOError, IndexError):
        return False

    last_log_date = last_line[:DATE_LEN]

    # if message date is other day than last log entry return True, else False
    if dt.now().strftime(DATE_FORMAT) != last_log_date:
        return True
    else:
        return False


def get_last_week():
    week_ago = dt.now() - timedelta(weeks=1)

    weekday = week_ago.isocalendar()[2] - 1
    last_monday = week_ago - timedelta(days=weekday)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


def get_week_range(date):
    date = dt.strptime(date, DATE_FORMAT)

    weekday = date.isocalendar()[2] - 1
    monday = date - timedelta(days=weekday)
    sunday = monday + timedelta(days=6)

    return monday, sunday


def parse_month_arg(arg):
    def is_int(arg):
        try:
            int(arg)
            return True
        except ValueError:
            return False

    if is_int(arg):
        # if it's only integer - it's only month number
        month = int(arg)
        if month < 1 or month > 12:
            sys.exit('Month must be in range from 1 to 12')
        return dt.now().year, month

    # otherwise argument must be in form 'YYYY-MM'
    year, month = arg.split('-')
    if is_int(year) and is_int(month):
        month = int(month)
        if month < 1 or month > 12:
            sys.exit('Month must be in range from 1 to 12')
        return int(year), month
    else:
        sys.exit('Argument in form of YYYY-MM is expected, e.g. 2015-9')


def get_month_range(arg, year=None):
    arg_w_year = '{}-{}'.format(year, arg) if year else arg
    year, month = parse_month_arg(arg_w_year)
    days_in_month = calendar.monthrange(year, month)[1]

    date_from = dt.strptime('{}-{:02}-01'.format(year, month), DATE_FORMAT)
    date_to = dt.strptime('{}-{:02}-{:02}'.format(year, month, days_in_month), DATE_FORMAT)

    return date_from, date_to


def get_last_month():
    month = dt.now().month - 1
    if month == 12:
        return get_month_range(month, year=dt.now().year-1)
    return get_month_range(month)


def print_stats(projects):
    work_time = sum([p.total_time for p in projects if not p.is_slack], timedelta())
    slack_time = sum([p.total_time for p in projects if p.is_slack], timedelta())

    work_string = 'Work: {}'.format(format_timedelta(work_time))
    slack_string = 'Slack: {}'.format(format_timedelta(slack_time))

    print(work_string)
    print(slack_string)


def format_timedelta(td):
    s = td.total_seconds()
    # Note: this takes the floor of the minute, it would be better to round to the nearest minute
    return '{}h {}m'.format(int(s // 3600), int(s % 3600 // 60))


def print_report(projects, date_from, date_to, colorize=False):
    # work = sorted([p for p in projects if not p.is_slack], key=lambda p: p.name)
    # slack = sorted([p for p in projects if p.is_slack], key=lambda p: p.name)
    # TODO: make the sorting be an argument so you can sort by time or name
    work = sorted([p for p in projects if not p.is_slack], key=lambda p: p.total_time, reverse=True)
    slack = sorted([p for p in projects if p.is_slack], key=lambda p: p.total_time, reverse=True)
    work_time = sum([p.total_time for p in work], timedelta())
    slack_time = sum([p.total_time for p in slack], timedelta())

    colorize_fn = _make_colorizer(colorize)

    dt_str = lambda d: d.strftime(DATE_FORMAT_FOR_STATS)

    report_dates_str = '{}'.format(dt_str(date_to)) if date_to == date_from else '{} to {}'.format(dt_str(date_from),
                                                                                                   dt_str(date_to))
    print(colorize_fn('report_header','Work report for {}'.format(report_dates_str)))
    print(colorize_fn('section_header', '{:-^80}'.format(' WORK {} '.format(format_timedelta(work_time)))))
    for p in work:
        print(p.project_report(work_time.total_seconds(), colorize_fn))
    print(colorize_fn('section_header', '{:-^80}'.format(' SLACK {} '.format(format_timedelta(slack_time)))))
    for p in slack:
        print(p.project_report(slack_time.total_seconds(), colorize_fn))


def _make_colorizer(colorize):
    if not colorize:
        return lambda category, s: s

    colors = {
        'project_name': 'green',
        'report_header': 'cyan',
        'section_header': 'yellow',
        'hashtag': 'cyan'
    }
    attrs = {
        'project_name': ['bold'],
        'report_header': ['bold'],
        'section_header': ['bold'],
    }

    def _colorize(category, str):
        return colored(str, color=colors.get(category, None), attrs=attrs.get(category, None))

    return _colorize

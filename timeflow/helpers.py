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
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_FORMAT = "%Y-%m-%d"
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


def read_log_file_lines():
    with open(LOG_FILE, 'r') as fp:
        return [line for line in fp.readlines() if _is_valid_line(line)]


def _is_valid_line(line):
    return not (line == '\n' or line.startswith('#'))


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


def find_date_line(lines, date_to_find, reverse=False):
    "Returns line index of lines, with date_to_find"
    len_lines = len(lines) - 1
    if reverse:
        lines = reversed(lines)
    for i, line in enumerate(lines):
        date_obj = dt.strptime(line[:DATE_LEN], DATE_FORMAT)
        date_to_find_obj = dt.strptime(date_to_find, DATE_FORMAT)

        if reverse and date_obj <= date_to_find_obj:
            return len_lines - i
        elif not reverse and date_obj >= date_to_find_obj:
            return i


def date_begins(lines, date_to_find):
    "Returns first line out of lines, with date_to_find"
    return find_date_line(lines, date_to_find)


def date_ends(lines, date_to_find):
    "Returns last line out of lines, with date_to_find"
    return find_date_line(lines, date_to_find, reverse=True)


def get_time(seconds):
    hours = seconds // 3600
    minutes = seconds % 3600 // 60
    return hours, minutes


def get_last_week():
    week_ago = dt.now() - timedelta(weeks=1)

    weekday = week_ago.isocalendar()[2] - 1
    last_monday = week_ago - timedelta(days=weekday)
    last_sunday = last_monday + timedelta(days=6)

    date_from = last_monday.strftime(DATE_FORMAT)
    date_to = last_sunday.strftime(DATE_FORMAT)
    return date_from, date_to


def get_week_range(date):
    date = dt.strptime(date, DATE_FORMAT)

    weekday = date.isocalendar()[2] - 1
    monday = date - timedelta(days=weekday)
    sunday = monday + timedelta(days=6)

    date_from = monday.strftime(DATE_FORMAT)
    date_to = sunday.strftime(DATE_FORMAT)
    return date_from, date_to


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


def get_month_range(arg):
    year, month = parse_month_arg(arg)
    days_in_month = calendar.monthrange(year, month)[1]

    date_from = '{}-{:02}-01'.format(year, month)
    date_to = '{}-{:02}-{:02}'.format(year, month, days_in_month)

    return date_from, date_to


def get_last_month():
    month = dt.now().month - 1
    if month == 12:
        return get_month_range(month, year=dt.now().year-1)
    return get_month_range(month)


def print_stats(work_time, slack_time, today_work_time):
    work_hours, work_minutes = get_time(sum(work_time))
    slack_hours, slack_minutes = get_time(sum(slack_time))

    work_string = 'Work: {:02}h {:02}m'.format(work_hours, work_minutes)
    slack_string = 'Slack: {:02}h {:02}m'.format(slack_hours, slack_minutes)

    print(work_string)
    print(slack_string)


def print_today_work_time(today_work_time):
    if today_work_time:
        today_hours, today_minutes = get_time(today_work_time)
        work_string = '\nToday working for: {:02}h {:02}m'.format(today_hours, today_minutes)
        print(work_string)


def create_report(report_dict, total_seconds, colorize_fn):
    reports = []
    report_dict = OrderedDict(sorted(report_dict.items()))
    hashtag_finder = re.compile(r'(#\w+)\b')
    colour_hash = lambda s: hashtag_finder.sub(lambda x: colorize_fn('hashtag', x.group(0)), s)


    for project in report_dict:
        report = ""
        project_report = report_dict[project]
        proj_seconds = 0
        for log in project_report:
            proj_seconds += project_report[log]
            hr, mn = get_time(project_report[log])

            # do not leave trailing space if there is no log
            time = '{}h {}m'.format(hr, mn)
            report += "    {:>7}".format(time)
            report += ": {}\n".format(colour_hash(colorize_fn('log', log))) if log else '\n'

        hr, mn = get_time(proj_seconds)

        report = (colorize_fn('project_name', project)
                  + ": {}h {}m ({:.2%})\n".format(hr, mn, proj_seconds / float(total_seconds))
                  + report)
        reports.append(report)
    return '\n'.join(reports)


def print_report(work_report_dict, slack_report_dict, work_time, slack_time, colorize=False):
    work_seconds, slack_seconds = sum(work_time), sum(slack_time)
    colorize_fn = _make_colorizer(colorize)
    work_report = create_report(work_report_dict, work_seconds, colorize_fn)
    slack_report = create_report(slack_report_dict, slack_seconds, colorize_fn)

    work_hours, work_minutes = get_time(work_seconds)
    slack_hours, slack_minutes = get_time(slack_seconds)

    print(colorize_fn('work_header', '{:-^80}'.format(' WORK {}h {}m '.format(work_hours, work_minutes))))
    print(work_report)
    print(colorize_fn('slack_header', '{:-^80}'.format(' SLACK {}h {}m '.format(slack_hours, slack_minutes))))
    print(slack_report)


def _make_colorizer(colorize):
    if not colorize:
        return lambda category, s: s

    colors = {
        'project_name': 'green',
        'work_header': 'cyan',
        'slack_header': 'yellow',
        'hashtag': 'cyan'
    }
    attrs = {
        'project_name': ['bold'],
        'work_header': ['bold'],
        'slack_header': ['bold'],
    }

    def _colorize(category, str):
        return colored(str, color=colors.get(category, None), attrs=attrs.get(category, None))

    return _colorize

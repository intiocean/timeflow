from collections import defaultdict, namedtuple
from datetime import datetime as dt, timedelta
import logging as logger

import re

from timeflow.helpers import DATETIME_FORMAT, LOG_FILE, DATE_FORMAT, format_timedelta

LogLine = namedtuple('LogLine', ['timestamp', 'message'])
Timelog = namedtuple('Timelog', ['start', 'end', 'duration', 'project', 'log', 'is_slack'])

_hashtag_finder = re.compile(r'(#[\w-]+)\b')


class Project(object):
    def __init__(self, name, is_slack):
        self.name = name
        self.is_slack = is_slack
        self.timelogs = []


    @property
    def total_time(self):
        return sum([tl.end - tl.start for tl in self.timelogs], timedelta())

    def add_timelog(self, timelog):
        """
        Add a
        :param timelog: `Timelog` object to add to this project
        """
        self.timelogs.append(timelog)

    def project_report(self, total_seconds, colorize_fn):
        colour_hash = lambda s: _hashtag_finder.sub(lambda x: colorize_fn('hashtag', x.group(0)), s)
        report = (colorize_fn('project_name', self.name)
                  + ": {} ({:.2%})\n".format(format_timedelta(self.total_time),
                                             self.total_time.total_seconds() / float(total_seconds)))
        # group timelogs by message so that we only get a single line per log message
        grouped = {}
        for tl in self.timelogs:
            grouped[tl.log] = grouped.get(tl.log, timedelta()) + tl.duration

        sorted_timelogs = sorted(grouped.items(), key=lambda el: el[1], reverse=True)

        for log, duration in sorted_timelogs:
            report += "    {:>7}".format(format_timedelta(duration))
            report += ": {}\n".format(colour_hash(colorize_fn('log', log))) if log else '\n'
        return report


def parse_message(message):
    """
    Parses the log as the message can be empty and identifies if this log is a slack log
    We strip the slack markers as well as whitespace.
    :return: `tuple` in the form of (is_slack, project, log) where project and log have had the slack markers removed
    """
    parsed_message = message.split(': ', 1)

    # if parsed message has only log stated, then the default project of Other is used
    if len(parsed_message) == 1:  # No colon found so either only a project has been put down or only a log
        split_message = parsed_message[0].split(None, 1)
        if len(split_message) == 1:
            project, log = parsed_message[0], ''
        else:
            project, log = 'Other', parsed_message[0]
    else:
        project, log = parsed_message

    is_slack = project.endswith("**") or log.endswith("**")
    return is_slack, project.rstrip('**').strip(), log.rstrip('**').strip()


def get_projects(date_from, date_to):
    lines = parse_lines()  # get ALL log lines as a dict of date to Logline objects
    res = defaultdict(dict)
    # {project_hash: Project(), project_hash: Project()} but return like [Project(), Project(), ...]
    for date, logs in lines.iteritems():
        if date_from <= date <= date_to:  # skip it if its not on a date we're interested in
            prev_dt = None
            for l in logs:
                if prev_dt is not None:  # if this is not the first entry of the day
                    is_slack, project, log = parse_message(l.message)
                    project_hash = ('{}**'.format(project) if is_slack else project).lower()  # Ignore case
                    if project_hash not in res:  # If the project doesn't exist on this date yet add it
                        res[project_hash] = Project(name=project, is_slack=is_slack)
                    res[project_hash].add_timelog(Timelog(prev_dt, l.timestamp, l.timestamp - prev_dt, project, log,
                                                          is_slack))

                    time_since_last_log = (l.timestamp - prev_dt).total_seconds()
                    if time_since_last_log < 0:
                        logger.warn('It looks like one of your time logs is out of order - time just jumped backwards!')
                prev_dt = l.timestamp
    return res.values()


def parse_lines():
    """Returns a dictionary keyed by date and with a list of objects representing each time log
    Each log line looks like this: [date] [time] [project]: [log message]
    """
    res = defaultdict(list)
    with open(LOG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):  # If there is any content on the line & skipping comments
                split = line.split(None, 2)
                if len(split) == 3:
                    date, time, message = split
                else:
                    message = ''
                    date, time = split
                timestamp = dt.strptime(date + ' ' + time, DATETIME_FORMAT)
                date = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                res[date].append(LogLine(timestamp, message))
        return dict(res)



def calc_time_diff(line, next_line):
    line_time = dt.strptime(
        "{} {}".format(line.date, line.time),
        DATETIME_FORMAT
    )
    next_line_time = dt.strptime(
        "{} {}".format(next_line.date, next_line.time),
        DATETIME_FORMAT
    )
    return (next_line_time - line_time).seconds
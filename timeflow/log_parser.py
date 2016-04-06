from collections import defaultdict, namedtuple
from datetime import datetime as dt
import logging as logger

from timeflow.helpers import DATETIME_FORMAT, LOG_FILE, DATE_FORMAT


LogLine = namedtuple('LogLine', ['timestamp', 'message'])
Timelog = namedtuple('Timelog', ['start', 'end', 'project', 'log', 'is_slack'])


def parse_message(message):
    "Parses message as log can be empty"
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

    return project, log


def find_slack(project, log):
    """
    Identifies if this log is a slack log and strips the slack markers as well as whitespace
    :param project: the project string
    :param log: the log string
    :return: `tuple` in the form of (is_slack, project, log) where project and log have had the slack markers removed
    """
    is_slack = project.endswith("**") or log.endswith("**")
    return is_slack, project.rstrip('**').strip(), log.rstrip('**').strip()


def get_timelogs():
    lines = parse_lines_new()
    res = defaultdict(list)
    for d, logs in lines.iteritems():
        prev_dt = None
        for l in logs:
            if prev_dt is not None:
                project, log = parse_message(l.message)
                is_slack, project, log = find_slack(project, log)
                res[d].append(Timelog(prev_dt, l.timestamp, project, log, is_slack))  # TODO: group by project here?
                time_since_last_log = (l.timestamp - prev_dt).total_seconds()
                if time_since_last_log < 0:
                    logger.warn('It looks like one of your time logs is out of order - time just jumped backwards!')
            prev_dt = l.timestamp
    return dict(res)


def parse_lines_new():
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


def calculate_report_and_get_time(date_from, date_to, today=False):
    """Creates and returns report dictionaries as well as work times

    Report dicts have form like this:
    {<Project>: {<log_message>: <accumulative time>},
                {<log_message1>: <accumulative time1>}}
    """
    work_time = []
    slack_time = []


    timelogs = get_timelogs()

    work_dict = defaultdict(lambda: defaultdict(int))
    slack_dict = defaultdict(lambda: defaultdict(int))
    for date, logs in timelogs.iteritems():
        if date_from <= date <= date_to:
            for l in logs:
                seconds = int((l.end - l.start).total_seconds())
                if l.is_slack:
                    slack_dict[l.project][l.log] += seconds
                    slack_time.append(seconds)
                else:
                    work_dict[l.project][l.log] += seconds
                    work_time.append(seconds)

    today_work_time = int((dt.now() - timelogs[date_from][0].start).total_seconds()) if today else None
    return work_dict, slack_dict, work_time, slack_time, today_work_time

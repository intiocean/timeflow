import argparse
from datetime import datetime as dt, timedelta, time
import os
import subprocess

from timeflow import __version__
from timeflow.helpers import (DATE_FORMAT, LOG_FILE, get_last_month, get_last_week, get_month_range, get_week_range,
                              print_stats, print_report, write_to_log_file, format_timedelta)

from timeflow.log_parser import get_projects


def log(args):
    write_to_log_file(args.message)


def edit(args):
    if args.editor:
        subprocess.call([args.editor, LOG_FILE])
    else:
        editor = os.environ.get('EDITOR')
        if editor in ('vi', 'vim'):  # open the file with the cursor on the last line of the file
            subprocess.call([editor, '+', LOG_FILE])
        elif editor:
            subprocess.call([editor, LOG_FILE])
        else:
            subprocess.call([
                "echo",
                "Set your default editor in EDITOR environment variable or \n"
                "call edit command with -e option and pass your editor, e.g.:\n"
                "timeflow edit -e vim",
            ])


def stats(args):
    if args.yesterday:
        yesterday_obj = dt.now() - timedelta(days=1)
        date_from = date_to = dt.combine(yesterday_obj, time.min)
    elif args.day:
        date_from = date_to = dt.strptime(args.day, DATE_FORMAT)
    elif args.week:  # TODO: this currently doesn't work. Fix or delete.
        date_from, date_to = get_week_range(args.week)
    elif args.last_week:
        date_from,  date_to = get_last_week()
    elif args.month:
        date_from,  date_to = get_month_range(args.month)
    elif args.last_month:
        date_from,  date_to = get_last_month()
    elif args._from and not args.to:
        date_from = dt.combine(dt.strptime(args._from, DATE_FORMAT), time.min)
        date_to = dt.combine(dt.now(), time.min)
    elif args._from and args.to:
        date_from = dt.combine(dt.strptime(args._from, DATE_FORMAT), time.min)
        date_to = dt.combine(dt.strptime(args.to, DATE_FORMAT), time.min)
    else:
        # default action is to show today's  stats
        date_from = date_to = dt.combine(dt.now(), time.min)

    projects = get_projects(date_from, date_to)

    if args.summary:
        print_stats(projects)
    else:
        print_report(projects, date_from, date_to, colorize=args.no_color)

    if date_from == date_to == dt.combine(dt.now(), time.min):  # then we are looking at today only
        earliest_start = min(min(tl.start for tl in p.timelogs) for p in projects)
        print('\nToday working for: {}'.format(format_timedelta(dt.now() - earliest_start)))


def set_log_parser(subparser):
    log_parser = subparser.add_parser("log", help="Create timelog message")
    log_parser.add_argument("message", nargs='?', default="", help="message that will be logged")
    # call log() function, when processing log command
    log_parser.set_defaults(func=log)


def set_edit_parser(subparser):
    edit_parser = subparser.add_parser("edit", help="Edit timelog file")
    edit_parser.add_argument("-e", "--editor", help="Explicitly set editor")
    # call edit() function, when processing edit command
    edit_parser.set_defaults(func=edit)


def set_stats_parser(subparser):
    stats_parser = subparser.add_parser("stats", help="Show how much time was spent working or slacking")

    stats_parser.add_argument("--today", action="store_true", help="Show today's work times (default)")
    stats_parser.add_argument("-y", "--yesterday", action="store_true", help="Show yesterday's work times")
    stats_parser.add_argument("-d", "--day", help="Show specific day's work times")

    stats_parser.add_argument("--week", help="Show specific week's work times")
    stats_parser.add_argument("--last-week", action="store_true", help="Show last week's work times")

    stats_parser.add_argument("--month", help="Show specific month's work times")
    stats_parser.add_argument("--last-month", action="store_true", help="Show last month's work times")

    stats_parser.add_argument("-f", "--from", help="Show work times from specific date", dest="_from")
    stats_parser.add_argument("-t", "--to", help="Show work times from to specific date")

    stats_parser.add_argument("-s", "--summary", action="store_true", help="Show a summary of stats")
    stats_parser.add_argument("--no-color", action="store_false", default=True, help="Don't colorize the stats report")

    # call stats() function, when processing stats command
    stats_parser.set_defaults(func=stats)


def parse_args(args):
    general_usage = """
General usage
-------------
When arriving in the morning to start the timer
    tf log

Logging time
    tf log "project: a commit message for my time"
    tf log project
    tf log "A log message without a project will get grouped into a project called Other"
    tf log "Coffee**: the asterisks at the end of the project mark this as a non-work"
    log"

Editing the time log
    tf edit

Showing time spent
    tf stats

For further options just run add --help to any of the above commands.

Opinionated usage
-----------------
The way I use it is that I have a category for each of my ongoing work/projects and then a few other categories
* Meeting
* Email
* Support: only for actual support
* Team: team discussions, questions, interuptions, fixing things for the team, etc
* Code Review: I copy a snippet from the URL of the PR to identify code reviews. eg. tools_bin/pull-requests/46

If its related to a Jira I add #EQ-1234 in the message"""
    parser = argparse.ArgumentParser(description=general_usage, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-v", "--version",
                        help="Show timeflow's version",
                        action="version",
                        version="timeflow {}".format(__version__))

    subparser = parser.add_subparsers(help="sub-command help")
    set_log_parser(subparser)
    set_edit_parser(subparser)
    set_stats_parser(subparser)

    return parser.parse_args(args)

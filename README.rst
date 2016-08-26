timeflow
========
simple CLI time logger, inspired by `gtimelog <https://github.com/gtimelog/gtimelog>`_

.. image:: img/description.png

Description
-----------
``timeflow`` is a simple CLI time logger, used for logging your activities and
featuring simple statistics and reporting capabilities

``timeflow`` can be called using either ``tf`` or ``timeflow`` commands

Install
-------

``pip install timeflow``

Written in ``python3``. Best user experience with ``python3``.

Tutorial
--------
::

    $ tf --help
    usage: tf [-h] [-v] {edit,stats,log} ...

    General usage
    -------------
    When arriving in the morning to start the timer
        tf log

    Logging time
        tf log "project: a commit message for my time"
        tf log project
        tf log "A log message without a project will get grouped into a project called Other"
        tf log "Coffee**: the asterisks at the end of the project mark this as a non-work"

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

    If its related to a Jira I add #EQ-1234 in the message

    positional arguments:
      {edit,stats,log}  sub-command help
        log             Create timelog message
        edit            Edit timelog file
        stats           Show how much time was spent working or slacking

    optional arguments:
      -h, --help        show this help message and exit
      -v, --version     Show timeflow's version

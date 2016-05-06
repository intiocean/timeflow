import sys

from timeflow import arg_parser


def main(args=sys.argv[1:]):
    args = arg_parser.parse_args(args)
    # if no command is passed, invoke help
    if hasattr(args, 'func'):
        args.func(args)
    else:
        arg_parser.parse_args(['--help'])


# Helpers which default some arguments and step into a single parser
def log(args=sys.argv[1:]):
    main(['log'] + args)


def stats(args=sys.argv[1:]):
    main(['stats'] + args)


def edit(args=sys.argv[1:]):
    main(['edit'] + args)

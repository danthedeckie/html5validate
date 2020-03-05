from .validator import validate


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            with open(f) as fh:
                validate(fh.read())
    else:
        validate(sys.stdin.read())

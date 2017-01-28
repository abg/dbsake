"""
dbsake.__main__
~~~~~~~~~~~~~~~

Executable package support
"""

import sys


def main():
    if __package__ == '':
        # To be able to run 'python wheel-0.9.whl/wheel':
        import os.path
        path = os.path.dirname(os.path.dirname(__file__))
        sys.path[0:0] = [path]
    import dbsake.cli
    sys.exit(dbsake.cli.main())


if __name__ == '__main__':
    sys.exit(main())

"""
dbsake.cmd
~~~~~~~~~

subcommands implemented for dbsake exist in this package namespace
"""
import pkgutil


def discover_commands():
    """Discover implemented commands in the dbsake.cmd package

    Loads all submodules in the dbsake.cmd package which are expected
    to implement a cli command.  These command autoregister themselves
    with the main dbsake cli.
    """
    walk_packages = pkgutil.walk_packages
    for importer, name, is_pkg in walk_packages(__path__, __name__ + '.'):
        loader = importer.find_module(name)
        loader.load_module(name)

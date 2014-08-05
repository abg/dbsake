"""
dbsake.core.util.template
~~~~~~~~~~~~~~~~~~~~~~~~

Support for loading jinja2 templates via pkgutil.

This is done to remove the dependence on setuptools, which
is often not a trivial dependency for the non-python savvy.
"""

import pkgutil

import jinja2

import dbsake


def jinja2_version():
    version = jinja2.__version__.partition('-')[0]
    return tuple([int(x) for x in version.split('.')])


class PEP302Loader(jinja2.BaseLoader):
    """Load templates from a python package.

    PEP302Loader is constructed with the name of the python package and path
    to the templates in that package::

        loader = PEP302Loader('mypackage', 'views')

    If the package path is not given, ``'templates'`` is assumed.

    Per default the template encoding is ``'utf-8'`` which can be changed
    by setting the `encoding` parameter to something else.
    """

    def __init__(self, package_name, package_path='templates',
                 encoding='utf-8'):
        self.package_name = package_name
        self.encoding = encoding
        self.package_path = package_path

    def get_source(self, environment, template):
        """Get the template source via pkgutil.get_data()

        If a resource is not found, a jinja2.TemplateNotFound error is raised.
        """
        resource_path = '/'.join([self.package_path, template])
        resource = pkgutil.get_data(self.package_name, resource_path)
        if resource is None:
            raise jinja2.TemplateNotFound(template)

        filename = None
        uptodate = None

        return resource.decode(self.encoding), filename, uptodate

    def list_templates(self):
        """This loader does not support enumerating available templates.

        :raises: TypeError
        """
        raise TypeError('this loader cannot iterate over all templates')


def escape_string(value):
    """Escape a string value by backslash escaping quotes and backslashes

    :returns: backslash escaped string
    """
    return value.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")


def create_environment(package_name, package_path='templates', **kwargs):
    """Create a new jinja2 environment using a PEP302Loader

    :param package_name: package_name to load templates from
    :param package_path: relative path in ``package_name`` to load templates
    :param kwargs: additional custom arguments to pass to jinja2.Environment
                   constructor
    :returns: jinja2.Environment instance
    """
    loader = PEP302Loader(package_name, package_path)
    kwargs['trim_blocks'] = True
    environment = jinja2.Environment(loader=loader, **kwargs)
    environment.filters['escape_string'] = escape_string
    environment.globals['__dbsake_version__'] = dbsake.__version__
    return environment

"""
dbsake.util.template
~~~~~~~~~~~~~~~~~~~~

Template support

This module wraps tempita and provides a simple template loader that loads
templates from a given package and renders the template content through
a tempita template.
"""

import pkgutil

from dbsake.thirdparty import tempita

def escape(value):
    """Escape a string value by backslash escaping quotes and backslashes

    :returns: backslash escaped string
    """
    return value.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")

def loader(package, prefix):
    """Create a template loader

    :param package: package to load from
    :param prefix: relative prefix to load resources from
    :returns: template renderer
    """
    def render(name, **kwargs):
        data = pkgutil.get_data(package, '/'.join([prefix, name]))
        return tempita.Template(data.decode('utf8'),
                                namespace=dict(escape=escape)).substitute(**kwargs)
    return render

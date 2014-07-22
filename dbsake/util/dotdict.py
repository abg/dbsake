"""
dbsake.util.dotdict
~~~~~~~~~~~~~~~~~~

Simple dotdict implementation
"""


class DotDict(dict):
    """Access dict elements as object attributes

    >>> b = DotDict(foo='bar', bar='baz')
    >>> b.foo
    'bar'
    >>> b.argh = 'castle'
    >>> b['argh']
    'castle'
    >>> b.argh
    'castle
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            # AttributeError: type object 'bunch' has no attribute 'baz'
            raise AttributeError('type %r has no attribute %r' %
                                 (self.__class__.__name__, name))

    def __setattr__(self, name, value):
        self[name] = value

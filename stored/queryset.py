from pickle import dumps, loads
from functools import partial
from ast import literal_eval
from copy import copy

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


class StoredQuerySetParser(object):
    Q = Q

    def get_Q(self, query_string, eval_locals={}, literals={}):
        literals = dict((k, literal_eval(v)) for (k, v) in literals.items())
        return eval(query_string.format(**literals), {'Q': Q}, eval_locals)


def manager_property():
    def fget(self):
        return self._manager

    def fset(self, name):
        self._manager_name = name
        self._manager = getattr(self.model, self._manager_name)

    def fdel(self):
        del self._foo
    return locals()


def default_manager_getter(self):
    return self()


class StoredQuerySetBase(StoredQuerySetParser):
    __slots__ = ['selector',
                 'query',
                 '_literals',
                 '_manager_name',
                 '_manager',
                 '_model']

    def literals(self, **literals):
        query = copy(self)
        query._literals.update(literals)
        return query

    def get_model(self):
        if not hasattr(self, '_model'):
            if isinstance(self.selector, int):
                kwargs = {'id': self.selector}
            else:
                kwargs = dict(zip(('app_label', 'model'),
                            self.selector.split('.')))
            self._model = ContentType.objects.get(**kwargs).model_class()
        return self._model

    model = property(get_model)

    manager = property(**manager_property())

    def __init__(self, query, model_selector, manager='objects', **literals):
        if not hasattr(self.__class__, manager):
            setattr(self.__class__, manager, property(default_manager_getter))

        self.selector = model_selector
        self.query = query
        self._literals = literals
        self.manager = manager

    def __getstate__(self):
        return dict((k, getattr(self, k)) for k in self.__slots__[:4])

    def __setstate__(self, dict):
        self.__init__(dict['query'],
                      dict['selector'],
                      dict['_manager_name'],
                      **dict['_literals'])

    def __call__(self, **eval_locals):
        return self.get_query_set(self.get_Q(self.query,
                                             eval_locals,
                                             self._literals))

    def __getattr__(self, name):
        return getattr(self.manager, name)


class FilterQuerySet(StoredQuerySetBase):
    def get_query_set(self, q):
        return self.manager.filter(q)


class ExcludeQuerySet(StoredQuerySetBase):
    def get_query_set(self, q):
        return self.manager.exclude(q)

StoredQuerySet = FilterQuerySet

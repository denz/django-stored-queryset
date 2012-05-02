from pickle import dumps, loads
from functools import partial, wraps
from ast import literal_eval
from copy import copy

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

def manager_property():
    def fget(self):
        return self._manager

    def fset(self, name):
        self._manager_name = name
        self._manager = copy(getattr(self.model, self._manager_name))

    def fdel(self):
        del self._foo
    return locals()


def default_manager_getter(self):
    return self()

def patch_query_set(stored):
    orig_get_query_set = stored.manager.get_query_set
    if not getattr(orig_get_query_set, 'eval_appent', False):
        @wraps(orig_get_query_set)
        def get_query_set(self, *args, **kwargs):
            return stored.get_query_set(orig_get_query_set(*args, **kwargs))
        get_query_set.eval_appent = True
        stored.manager.get_query_set = get_query_set.__get__(stored.manager,
                                                             stored.manager.__class__)

class FilterQuerySet(object):
    Q = Q
    __slots__ = ['selector',
                 'query',
                 '_literals',
                 '_manager_name',
                 '_manager',
                 '_model',
                 '_eval_locals']
    
    def get_query_set(self, queryset):
        literals = dict((k, literal_eval(v)) for (k, v) in self._literals.items())
        query = eval(self.query.format(**literals), {'Q': FilterQuerySet.Q}, self._eval_locals)
        return queryset.filter(query)

    def literals(self, **literals):
        self._literals.update(literals)
        return self

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
        self._eval_locals = {}
        patch_query_set(self)

    def __getstate__(self):
        return dict((k, getattr(self, k)) for k in self.__slots__[:4])

    def __setstate__(self, dict):
        self.__init__(dict['query'],
                      dict['selector'],
                      dict['_manager_name'],
                    **dict['_literals'])

    def __call__(self, **eval_locals):
        self._eval_locals.update(eval_locals)
        return self

    def __getattr__(self, name):
        return getattr(self.manager, name)

StoredQuerySet = FilterQuerySet

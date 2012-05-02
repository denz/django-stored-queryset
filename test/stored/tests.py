from pickle import loads, dumps

from django.test import TestCase
# from django.db.models import DoesNotExist

from django.contrib.contenttypes.models import ContentType

from stored.queryset import StoredQuerySetBase, FilterQuerySet, ExcludeQuerySet
from models import TModel, Rel0
import sys

from stored.boolean import parse, BooleanAlgebra, Symbol


class StoredQuerySetBaseTestCase(TestCase):
    def test_get_model(self):
        self.assert_(StoredQuerySetBase('', 3).model == TModel)
        self.assert_(StoredQuerySetBase('', 1).model != TModel)
        self.assert_(StoredQuerySetBase('', 'stored.tmodel').model == TModel)
        self.assertRaises(ContentType.DoesNotExist, 
                            lambda:StoredQuerySetBase('', 'stored.zzzztmodel').model)

    def test_get_manager(self):
        self.assert_(StoredQuerySetBase('', 3).manager.model == TModel)
        self.assert_(StoredQuerySetBase('', 1).manager.model != TModel)

        self.assert_(StoredQuerySetBase('', 3, 
                                manager='_default_manager').manager == TModel._default_manager)

# query = FilterQuerySet("Q(headline='test')&Q(id__in={idlist})|Q(related__in=related)|Q(headline={headline})")


# q1 = query(related=A.objects.all())
# q2 = q1.literals(idlist='[4,5,6]', headline='someheadline')
# q1.objects.all() - with idlist = [1,2,3], headline ='someheadline'
# q2.objects.all() - with idlist = [4,5,6], headline ='someheadline'
# q1 != q2

def flatten(i):
    return [k[0] for k in i]

class FilterQuerySetTestCase(TestCase):
    # q0 = "Q(headline='{headline}')&Q(id__in={idlist})"
    queries = [{'query':"Q(headline__startswith='{headline}')",
                    'selector':'stored.tmodel',
                    'literals':{'headline':'"head1"'},
                    'result':[1, 10],
                },
                {'query':"Q(headline__startswith='{headline}')&Q(id__in={idlist})",
                    'selector':'stored.tmodel',
                    'literals':{'headline':'"head1"', 'idlist':'[1,10]'},
                    'override_literals':{'idlist':'[1,]'},
                    'result':[1, 10],
                    'override_result':[1,]
                },                
                {'query':"Q(related__in=related_qset)",
                    'selector':'stored.tmodel',
                    'eval':{'related_qset':lambda:Rel0.objects.all()[:1]},
                    'result':[1,],
                },
                {'query':"Q(related__in=related_qset)&~Q(id__in=[2,3])",
                    'selector':'stored.tmodel',
                    'eval':{'related_qset':lambda:Rel0.objects.all()[:1]},
                    'result':[1,],
                },
                {'query':"Q(related__in=related_qset)&~Q(id__in={idlist})",
                    'selector':'stored.tmodel',
                    'eval':{'related_qset':lambda:Rel0.objects.all()[:1]},
                    'literals':{'idlist':'[2,3]'},
                    'override_literals':{'idlist':'[1,2,3]'},
                    'result':[1,],
                    'override_result':[],
                },

                ]

    def setUp(self):
        for i in range(10):
            Rel0.objects.create()
        for i in range(1, 11):
            t = TModel.objects.create(headline='head%s'%i)
            t.related.add(Rel0.objects.all()[i-1])
            t.save()

    def test_queries(self):
        for params in self.queries:
            query = FilterQuerySet(params['query'], params['selector'], 
                                        **params.get('literals', {}))
            
            evals = dict((k, v()) for (k,v) in params.get('eval', {}).items())
            evaluated_query = query(**evals)
            result = evaluated_query.values_list('id')

            restored_query = loads(dumps(query))
            restored_result = restored_query(**evals).values_list('id')

            if params.get('override_literals', {}):
                override_result = query.literals(**params['override_literals'])(**evals).values_list('id')
                restored_overrride_result = restored_query.literals(**params['override_literals'])\
                                            (**evals).values_list('id')
                self.assert_(query.literals(**params['override_literals']) is not query)

            
            self.assert_(flatten(result) == params['result'])
            self.assert_(flatten(restored_result) == params['result'])
            self.assert_(flatten(restored_result) == params['result'])
            if params.get('override_literals', {}):
                self.assert_(flatten(override_result) == params['override_result'])
                self.assert_(flatten(restored_overrride_result) == params['override_result'])

    def test_manager_attribute(self):
        pass
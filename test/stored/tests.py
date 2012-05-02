from pickle import loads, dumps

from django.test import TestCase
# from django.db.models import DoesNotExist

from django.contrib.contenttypes.models import ContentType

from stored.queryset import FilterQuerySet
from models import TModel, Rel0
import sys

from stored.boolean import parse, BooleanAlgebra, Symbol


class StoredQuerySetBaseTestCase(TestCase):
    def test_get_model(self):
        self.assert_(FilterQuerySet('Q(a=1)', 3).model == TModel)
        self.assert_(FilterQuerySet('Q(a=1)', 2).model != TModel)
        self.assert_(FilterQuerySet('Q(a=1)', 'stored.tmodel').model == TModel)
        self.assertRaises(ContentType.DoesNotExist, 
                            lambda:FilterQuerySet('Q(a=1)', 'stored.zzzztmodel').model)

    def test_get_manager(self):
        self.assert_(FilterQuerySet('Q(a=1)', 3).manager.model == TModel)
        self.assert_(FilterQuerySet('Q(a=1)', 2).manager.model != TModel)


def flatten(i):
    return [k[0] for k in i]

class FilterQuerySetTestCase(TestCase):
    queries = [
                {'query':"Q(headline__startswith='{headline}')",
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
                restored_override_result = restored_query.literals(**params['override_literals'])\
                                            (**evals).values_list('id')
                # self.assert_(query.literals(**params['override_literals']) is not query)

            
            self.assert_(flatten(result) == params['result'],
                         '1:%s:%s!=%s'%(params['query'],
                                        flatten(result),
                                        params['result']))
            self.assert_(flatten(restored_result) == params['result'],
                         '2:%s:%s!=%s'%(params['query'], 
                                        flatten(restored_result),
                                        params['result']))
            self.assert_(flatten(restored_result) == params['result'],
                         '3:%s:%s!=%s'%(params['query'],
                                        flatten(restored_result),
                                        params['result']))
            if params.get('override_literals', {}):
                self.assert_(flatten(override_result) == params['override_result'],
                         '4:%s:%s!=%s'%(params['query'],
                                        flatten(override_result),
                                        params['override_result']))
                self.assert_(flatten(restored_override_result) == params['override_result'],
                         '5:%s:%s!=%s'%(params['query'],
                                        flatten(restored_override_result), 
                                        params['override_result']))

    def test_query_literals(self):
        query = FilterQuerySet("Q(headline__startswith='{headline}')&Q(id__in={idlist})",
                               'stored.tmodel')
        self.assertRaises(KeyError, lambda:query.objects.all())

        query.literals(headline='"head"')
        self.assertRaises(KeyError, lambda:query.objects.all())
        query.literals(idlist='[1,2]')
        self.assert_(flatten(query.objects.all().values_list('id')) == [1,2])

    def test_query_evals(self):
        query = FilterQuerySet("Q(headline__startswith=headline)&Q(id__in={idlist})",
                               'stored.tmodel', idlist='[1,2]')
        self.assertRaises(NameError, lambda:query.objects.all())

        query(headline='head')
        self.assert_(flatten(query.objects.all().values_list('id')) == [1,2])

    def test_query_evals_with_literals0(self):
        query = FilterQuerySet("Q(headline__startswith=headline)&Q(id__in={idlist})",
                               'stored.tmodel')
        self.assertRaises(KeyError, lambda:query.objects.all())

        query.literals(idlist='[1,2]')
        self.assertRaises(NameError, lambda:query.objects.all())

        query(headline='head')
        self.assert_(flatten(query.objects.all().values_list('id')) == [1,2])


    def test_query_evals_with_literals1(self):
        query = FilterQuerySet("Q(headline__startswith=headline)&Q(id__in={idlist})",
                               'stored.tmodel')
        query.literals(idlist='[1,2]')(headline='head')
        self.assert_(flatten(query.objects.all().values_list('id')) == [1,2])

    def test_query_evals_with_literals2(self):
        query = FilterQuerySet("Q(headline__startswith=headline)&Q(id__in={idlist})",
                               'stored.tmodel')
        query(headline='head').literals(idlist='[1,2]')
        self.assert_(flatten(query.objects.all().values_list('id')) == [1,2])

    def test_query_evals_with_literals3(self):
        query = FilterQuerySet("Q(headline__startswith=headline)&Q(id__in={idlist})",
                               'stored.tmodel')
        query(headline='head').literals(idlist='[1,2]')
        query.literals(idlist='[3,4]')
        self.assert_(flatten(query.objects.all().values_list('id')) == [3,4])

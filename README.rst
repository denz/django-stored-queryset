OUTLINE
=======


Persistent representation of django QuerySet`s.

Quick creation of simple search functionality without custom SQL or implicit markers/ids/indexes storing.

EXAMPLES
========

Trivial example
---------------

::

    from stored.queryset import FilterQuerySet
    q = FilterQuerySet('Q(text__icontains="sometext")', 'someapp.somemodel')
    q.objects.all() #outputs all 

    loads(dumps(q)).objects.all() #same result



Simple with literals
--------------------

::

    #define default literals
    q0 = FilterQuerySet('Q(text__icontains="{literal_text}")', 
                        'someapp.somemodel', 
                        literal_parameter='"sometext"')

    #new queryset with different `literal_text` value
    q1 = q0.literal(literal_text='"some_other_text"').objects.all()
    #literals are parsed with safe `ast.literal_eval` and can be taken from user input

    #q1 can be pickled and thus user search can be stored in db
    #if to keep different `FilterQuerySet` for each user.
    loads(dumps(q1)).objects.all() #same result


More complex - user specific search with related fields and persistent parameters
---------------------------------------------------------------------------------

models.py::

    from django.db import models
    from django.contrib.auth.models import User

    from stored.queryset import FilterQuerySet

    class RelatedModel(models.Model):
        user = models.ForeignKey(User, blank=True, null=True)#or maybe MtM
        rating = models.IntegerField()

    class SomeModel(models.model):
        text = models.CharField()
        related_field = models.ForeignKey(RelatedModel)

views.py::

    search_query = 'Q(text__icontains="{search}")\
    &Q(related_field__in=related.filter(rating__gte={min_related_rating}))'

    default_search_queryset = \
        FilterQuerySet(query, 'someapp.somemodel', min_related_rating='3')

    def view(request):
        if not request.user.is_anonymous():
            profile = request.user.get_profile()
            query = loads(profile.search) \
                            if profile.search \
                            else default_search_queryset)

            #query.objects.all() will raise an exception - 
            #we have to define `related` variable and `search` literal
            
            related = RelatedModel.objects.filter(Q(user=request.user)|Q(user__in=[None, '']))
            
            def store_search(query):
                profile.search = dumps(query)
                profile.save()
        else:
            query = default_search_queryset
            related = RelatedModel.objects.filter(Q(user__in=[None, '']))
            def store_search(query):
                pass
        
        #define evaluated variables
        actual_query = query(related=related)

        #ALERT: NEVER PASS USER INPUT AS EVALUATED VARIABLES
        #use literals for that

        if request.REQUEST.get('search', None): #bonus: previus search stored too
            actual_query.literals(search=request.REQUEST['search'])


        if request.REQUEST.get('min_rating', None): #override min_rating if required
            actual_query.literals(min_related_rating=int(request.REQUEST['min_rating']))

        #now we can store it together with last search string and `min_related_rating` parameter
        store_search(actual_query)
        #NOTICE. `related` and any evaluated variables will NOT be stored 
        #so next time we have to call query with `related` again.

        return render_to_response('search.html', {'items':actual_query.objects})
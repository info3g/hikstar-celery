# -*- coding: utf-8 -*-
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from hikster.location.serializers import \
    LocationSerializer, \
    PointOfInterestSerializer, \
    PointOfInterestTypeSerializer
from hikster.location.models import Location, PointOfInterest, PointOfInterestType
from hikster.location.tasks import send_deletion_email_task

from hikster.helpers import pagination, permissions


class LocationViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for the location resource.

    Include and Exclude :
    -Include and exclude expect a comma-separated list of fields (ex. name,contact). They are mutually exclusive so I
     would advise not to use them together.

    Expand :
    By default, relations are expressed as a list of ids to the relevent resource (e.g. contact: [1, 2]).
    This is to improve performance. If you need access to these object, you can use the parameter "expand"
    (e.g. "/?expand=location") which will return the "expanded" object. If the expanded object itself contains another
    nested object, you can access the nested object like so "expand=contact,location.address,location.contact".
    The following objects can be expanded for the trail object:
    - address
    - contact
    - images

    The resource accepts the following query parameters (params appended with * are mandatory):
    - search_term [type: string] (e.g. Mont Saint-Bruno)

    Value for search_term is a string of the form "{location_name} ({id})"

    Exposes custom resource for autosuggest which takes the same parameters

    Example request
    /locations/autosuggest/?search_term=Mon
    /locations/8
    /locations/8/?expand=address,contact,images
    
    
    """
    queryset = Location.objects_with_eager_loading.all()
    serializer_class = LocationSerializer
    pagination_class = pagination.CustomPageNumberPagination
    permission_classes = (permissions.IsOwnerOrReadOnly,)

    def get_queryset(self):
        queryset = self.queryset

        # [fbrousseau 2017-03-20: check to do prefetch_related only on GET request (see
        # https://github.com/tomchristie/django-rest-framework/issues/2442#issuecomment-71006996)]
        if self.action == 'retrieve' or self.action == 'list':
            queryset = queryset.prefetch_related("contact", "images")

        data = self.request.query_params
        search_term = data.get("search_term")

        if search_term:
            if "(" in search_term and ")" in search_term:
                terms = str(search_term).rsplit(" ", 1)
                id = str(terms[1]).replace("(", "").replace(")", "")
                location = queryset.filter(location_id=id)
            else:
                try:
                    location = queryset.get(name=search_term)
                except MultipleObjectsReturned:
                    location = queryset.filter(
                        name__icontains=search_term
                    )
                except ObjectDoesNotExist:
                    location = queryset.filter(
                        name__icontains=search_term
                    )
            return location
        else:
            return queryset

    def get_serializer_context(self):
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        # Pop problematic data that can't be serialized directly
        serializer = self.get_serializer(
            data=request.data,
            expanded_fields='contact,images,address'
        )
        if serializer.is_valid():
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
            expanded_fields="contact,images,address"
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        username = kwargs.get('parent_lookup_username', None)

        queryset = self.get_queryset()

        if username:
            queryset = queryset.filter(owner__user__username=username)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @list_route(methods=['get'])
    def autosuggest(self, request):
        """
        List resource that returns suggestions for autocomplete.
        :param request: Request object with the current term to look for
        :return: The reduced set of data containing the id, name and type
        """
        location_kwargs = {"name__unaccent__icontains": request.query_params.get("search_term")}

        # create query for

        searched_location = Location.objects.filter(**location_kwargs).distinct()[:12]
        serialized_data = LocationSerializer(searched_location, context={'request': request}, many=True)
        return Response(serialized_data.data)

    @detail_route(methods=["post"], permission_classes=[permissions.SimpleIsOwnerOrReadOnly])
    def delete(self, request, pk=None):
        instance = self.get_object()

        # Modify object to pending deletion state
        instance.deletion_pending = True
        instance.save(update_fields=['deletion_pending'])

        # Send mail
        sender = request.user.email
        receiver = "support@hikster.com"
        subject = "Demande de supression - {name}".format(name=instance.name)
        message = ""

        send_deletion_email_task.delay(subject=subject, message=message, from_email=sender, recipient_list=[receiver])

        # Return object to be deleted
        serializer = self.get_serializer(instance)
        return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)


class PointOfInterestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for the trail resource.

    Include and Exclude :
    -Include and exclude expect a comma-separated list of fields (ex. name,contact). They are mutually exclusive so I
     would advise not to use them together.

    Expand :
    By default, relations are expressed as a list of ids to the relevent resource (e.g. contact: [1, 2]).
    This is to improve performance. If you need access to these object, you can use the parameter "expand"
    (e.g. "/?expand=location") which will return the "expanded" object. If the expanded object itself contains another
    nested object, you can access the nested object like so "expand=contact,location.address,location.contact".
    The following objects can be expanded for the trail object:
    - address
    - contact
    - images
    - location
    - type

    The resource accepts the following poi_kwargsing parameters (params appended with * are mandatory) :
    - search_term [type: string] (e.g. Mont Saint-Bruno (id))
    - category type: array (e.g. 1,4,6)
    - coordinate to rank result by distance from this point

    Value for search_term is a string of the form "{location_name} ({id})"
    Values for "category" are 1=Hébergement, 3=Stationnement, 4=Activité, 5=Restaurant, 6=Autre

    Example request = /point-of-interests/?search_term=toilettes&category=1,4,5,6

    """
    queryset = PointOfInterest.objects_with_eager_loading.filter(
        Q(visible_in_map=1) & (~Q(category__in=[1, 4, 5]) | Q(premium=True)))
    serializer_class = PointOfInterestSerializer
    pagination_class = pagination.CustomPageNumberPagination

    def get_queryset(self):
        queryset = super(PointOfInterestViewSet, self).get_queryset()

        search_term = self.request.GET.get('search_term', None)
        category = self.request.GET.get('category', None)
        coord = self.request.GET.get('coord', None)

        #
        # Check to do prefetch_related only on GET request:
        #
        #   https://github.com/tomchristie/django-rest-framework/issues/2442#issuecomment-71006996
        #
        if self.action in ['retrieve', 'list']:
            queryset = queryset.prefetch_related(
                'contact',
                "images"
            )
        #
        # Retrieve a single trail
        #
        if self.action == 'retrieve':
            return queryset

        #
        # Constrain by search term
        #
        if search_term:
            queryset = queryset.filter(
                Q(name__unaccent__icontains=search_term)
                | Q(type__name__unaccent__icontains=search_term)
                | Q(description__unaccent__icontains=search_term)
            )

        #
        # Constrain by category
        #
        if category:
            categories = [int(cat_id) for cat_id in category.split(',')]
            queryset = queryset.filter(category__in=categories)

        #
        # Order by distance, if coordinates provided
        #
        if coord:
            point = Point(*[float(x) for x in coord.split(',')], srid=4326)
            queryset = queryset.annotate(
                distance=Distance('shape', point)
            ).order_by('distance')

        return queryset

    def get_serializer_class(self):
        return PointOfInterestSerializer


class PointOfInterestTypeViewSet(viewsets.ModelViewSet):
    queryset = PointOfInterestType.objects.all()
    serializer_class = PointOfInterestTypeSerializer

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Polygon
from django.db.models import Q
from django.db.models import QuerySet
from rest_framework import viewsets, status
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from hikster.helpers import functions, pagination, permissions
from hikster.hike.models import Activity, Event, EventTrailSection, Trail, TrailSection
from hikster.hike.serializers import (
    ActivitySerializer,
    EventSerializer,
    EventTrailSectionSerializer,
    Trail3DSerializer,
    TrailSectionSerializer,
    TrailSerializer,
)
from hikster.location.models import LOCATION_NETWORK, Location


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.values()
    serializer_class = ActivitySerializer


class TrailSectionViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = TrailSection.objects_with_eager_loading.all()
    serializer_class = TrailSectionSerializer
    pagination_class = pagination.CustomPageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    """
    ViewSet for the TrailSection resource.

    TrailSection model is modified in 2017/07 in order to implement Dynamic Linear Segmentation - users create trail sections
    and connect trailsections into trails, via eventtrailsection and event.

    We set up a spatial relationship here using SQL queries for trailsection and Location models in order for admin users
    to only view and modify the trail sections inside of their territory

    """

    def get_queryset(self) -> QuerySet:
        queryset = self.queryset
        arguments = {
            key: value for key, value in self.request.self.request.GET.items() if value
        }

        ids = arguments.pop("ids", None)
        location = arguments.pop("location", None)

        if ids:
            trailsections_to_find = ids.split(",")
            return queryset.filter(pk__in=trailsections_to_find)

        if location:
            # first, get all location ids from the url - location_id_list
            # second, get only the location objects of these ids in Location table
            # third, loc_shapes is an list of the shape attr of all location objects
            # last, filter all the query sets using GeoJson shape__within all the shapes in location_shapes
            location_id_list = [int(loc_id) for loc_id in location.split(",")]
            location_obj_list = Location.objects.filter(
                location_id__in=location_id_list
            )

            location_buffered_shapes = [
                location_obj.shape.buffer(0.02)
                for location_obj in location_obj_list
                if location_obj.shape is not None
            ]

            # Turn the list of location shapes into a list of Q objects
            queries = [Q(shape__within=shape) for shape in location_buffered_shapes]
            # Take one Q object from the list
            query = queries.pop()
            # Or the Q object with the ones remaining in the list
            for item in queries:
                query |= item

            queryset = queryset.filter(query)
            return queryset

        return queryset

    def get_serializer_context(self):
        return {"request": self.request}

    def get_serializer_class(self):
        return TrailSectionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            header = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=header
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, partial=partial, data=request.data)
        if serializer.is_valid():
            self.perform_update(serializer)
            header = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK, headers=header)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *arg, **kwargs):
        queryset = self.get_queryset()

        if "location" in request.self.request.GET:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class TrailViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for the trail resource.

    Each endpoint accepts the following querystring parameters: include, exclude and expand.

    Include and Exclude :
    -Include and exclude expect a comma-separated list of fields (ex. name,contact). They are mutually exclusive so I
     would advise not to use them together.

    Expand :
    By default, relations are expressed as a list of ids to the relevent resource (e.g. contact: [1, 2]).
    This is to improve performance. If you need access to these object, you can use the parameter "expand"
    (e.g. "/?expand=location") which will return the "expanded" object. If the expanded object itself contains another
    nested object, you can access the nested object like so "expand=contact,location.address,location.contact".
    The following objects can be expanded for the trail object:
    - images
    - location
    - location.address
    - location.contact
    - location.images

    The resource accepts the following filtering parameters :

    - ID trail
    - difficulty [type: int] (e.g. 0 | 1 | 2 | 3 | 4 | 5)
    - activities [type: int] (e.g. 0 | 1 | 2 | 3)
    - length [type: string] (e.g. "0" | "0-2000" | "2000-5000" | "5000-10000" | "10000"). Expressed in meter.
    - dog_allowed [type: boolean] (e.g. 1 | 0)
    - types [type: int]
    - Constrain by a bounding box
    - Constrain by a location

    Values for "difficulty" are 0=Toutes les difficultés, 1=Débutant, 2=Modéré, 3=Intermédiaire, 4=Soutenu, 5=Exigeant

    Values for "activity" are (Cf hike.activities) 0=Tous les sports, 1=Rando, 2=Raquette, 3=Randonnée hivernale, 4=Vélo de montagne, 5=Fatbike, 6=Vélo, 7=Ski de fond, 8=Équitation

    Values for length are like in the example

    Here are some exemple of requests :
    /trails/59072/?expand=location,location.address,location.contact,images
    /trails/difficulty=2&date=2&length=2-5&dog_allowed=true
    /trails/?difficutly=1,2,3
    /trails/?activities=1,2,3
    /trails/?length=0-5000
    /trails/?dog_allowed=1
    /trails/?types=1,2,3
    /trails/?min_lng=-73.587738&min_lat=45.504050&max_lng=-73.587730&max_lat=45.504058
    /trails/?min_lng=-73.587738&min_lat=45.504050&max_lng=-73.587730&max_lat=45.504058&difficulty=1

    """

    queryset = Trail.objects_with_eager_loading.all()
    pagination_class = pagination.CustomPageNumberPagination
    permission_classes = (permissions.IsOwnerOrReadOnly,)
    serializer_class = TrailSerializer

    def get_queryset(self) -> QuerySet:
        """
        Custom queryset to filter trails

        :return: All, one or a filtered set of trails

        """
        loc_id = self.request.GET.get("loc", None)
        arg_locations = self.request.GET.get("locations", None)
        min_lng = self.request.GET.get("min_lng", None)
        min_lat = self.request.GET.get("min_lat", None)
        max_lng = self.request.GET.get("max_lng", None)
        max_lat = self.request.GET.get("max_lat", None)
        ids = self.request.GET.get("ids", None)
        activity_id = self.request.GET.get("activity", None)
        activities = self.request.GET.get("activities", None)
        types = self.request.GET.get("types", None)
        difficulty = self.request.GET.get("difficulty", None)
        length = self.request.GET.get("length", None)
        dog_allowed = self.request.GET.get("dog_allowed", None)
        search_term = self.request.GET.get("search_term", None)

        if arg_locations:
            location_ids = list(map(int, arg_locations.split(",")))
            is_multilocation = True
        else:
            location_ids = ()
            is_multilocation = False

        # Check to do prefetch_related only on GET request:
        #
        #   https://github.com/tomchristie/django-rest-framework/issues/2442#issuecomment-71006996
        #
        queryset = super().get_queryset()
        if self.action in ["retrieve", "list"]:
            queryset = queryset.prefetch_related(
                "trail_sections", "images", "location__contact", "location__images"
            )

        #
        # Retrieve a single trail
        #
        if self.action == "retrieve":
            return queryset

        # TODO: move this to search view
        if search_term:
            trail_kwargs = {}
            location = functions.get_location(search_term)
            # If we have multiple returned results, we get the best one with fuzzy string matching
            location = (
                functions.get_closest_match(search_term, location)
                if type(location) is QuerySet
                else location
            )

            if location["type"] == 11:
                trail_kwargs["location_id"] = location["location_id"]
            elif location["type"] == 10:
                trail_kwargs["region_id"] = location["location_id"]
            else:
                trail_kwargs["shape__dwithin"] = (location["shape"], 0)

            queryset = queryset.filter(**trail_kwargs)

        #
        # Constrain by a location
        #
        if loc_id or arg_locations:

            if is_multilocation:
                locs = Location.objects.filter(location_id__in=location_ids)
                location = None
                is_loc_netw = False
            else:
                locs = Location.objects.filter(location_id=loc_id)
                location = locs.first()
                is_loc_netw = location and location.type == LOCATION_NETWORK

            if not locs.exists():
                return queryset.none()

            if is_multilocation or is_loc_netw:
                queryset = queryset.filter(location__in=locs)
            elif location:
                queryset = queryset.filter(shape__intersects=location.shape)
            else:
                return queryset.none()

        #
        # Constrain by a bounding box
        #
        if min_lng and min_lat and max_lng and max_lat:
            bbox_coord = (min_lng, min_lat, max_lng, max_lat)
            bbox = Polygon.from_bbox(bbox_coord)
            center = bbox.centroid
            center.srid = 4326
            queryset = (
                queryset.filter(shape__bboverlaps=bbox)
                .annotate(distance=Distance("shape", center))
                .order_by("distance")
            )

        #
        # Constrain by a list of trail ids
        #
        if ids:
            queryset = queryset.filter(pk__in=ids.split(","))

        #
        # Filter by activity
        #
        if activity_id:
            activity_id = activity_id.split(",")
            queryset = queryset.filter(activities__activity_id__in=activity_id)

        #
        # Filter by activities
        #
        if activities:
            queryset = queryset.filter(
                activities__activity_id__in=activities.split(",")
            )

        #
        # Filter by path_type
        #
        if types:
            queryset = queryset.filter(path_type__in=types.split(","))

        #
        # Filter by difficulty
        #
        if difficulty:
            difficulty = difficulty.split(",")
            queryset = queryset.filter(activities__difficulty__in=difficulty)

        #
        # Filter by length
        #
        if length:
            length_bounds = length.split("-")
            length_min = float(length_bounds[0])
            queryset = queryset.filter(total_length__gte=length_min)
            if len(length_bounds) > 1:
                length_max = float(length_bounds[1])
                queryset = queryset.filter(total_length__lte=length_max)

        #
        # Filter by dogs allowed
        #
        if dog_allowed:
            dog_allowed = int(dog_allowed) == 1
            queryset = queryset.filter(location__dog_allowed=dog_allowed)

        return queryset.order_by("trail_id")

    def _filter_by_coord(self, queryset, lng, lat):
        """
        Performs a query based on a set of coordinates.
        :return: a queryset
        """
        pass

    def get_serializer_context(self):
        return {"request": self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, expanded_fields="images")
        if serializer.is_valid():
            self.perform_create(serializer)
            header = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=header
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.get("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
            expanded_fields="images,activities",
        )
        if serializer.is_valid():
            self.perform_update(serializer)
            header = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK, headers=header)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        username = kwargs.get("parent_lookup_username", None)
        location = kwargs.get("parent_lookup_location", None)

        queryset = self.get_queryset()

        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)
        if username:
            queryset = queryset.filter(owner__user__username=username)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        if location:
            queryset = queryset.filter(location_id=location)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @list_route(methods=["get"])
    def get_trails_by_trail_section(self, request) -> Response:

        """
        Function to get the relevent trail when clicking on a trail_section from the map
        :param request:
        :return: Response object with the trail objects
        """

        data = request.self.request.GET
        arguments = {}

        for key, value in data.items():
            if value:
                arguments[key] = value

        hikes = self.queryset.filter(
            trail_sections__trail_id=int(arguments["trailSectionId"])
        )
        serializer = self.get_serializer(hikes, many=True)
        return Response(serializer.data)

    @list_route(methods=["get"])
    def showcase(self, request) -> Response:
        """
        Get the trails to showcase on the frontpage
        :param request:
        :return: Response object with the 6 trails to showcase
        """
        showcase_hikes = self.get_queryset().filter(
            trail_id__in=(6474, 6890, 6378, 6525, 7012, 7994)
        )
        serializer = self.get_serializer(showcase_hikes, many=True)
        return Response(serializer.data)


class Trail3DViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Trail.objects.values("trail_id", "shape")
    serializer_class = Trail3DSerializer
    pagination_class = pagination.CustomPageNumberPagination


class EventViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class EventTrailSectionViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = EventTrailSection.objects.all()
    serializer_class = EventTrailSectionSerializer

    def create(self, request, *args, **kwargs):
        trailsectionList = request.data["trailsections"]

        serializer = self.get_serializer(data=trailsectionList, many=True)
        if serializer.is_valid():
            self.perform_create(serializer)
            header = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=header
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

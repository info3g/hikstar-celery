def pretty_time_delta(seconds):
    seconds = int(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if len(str(minutes)) != 2:
        minutes = "0" + str(minutes)

    return '{0}:{1}'.format(hours, minutes)


def get_closest_match(query: str, choices: dict) -> dict:
    from fuzzywuzzy import process
    result = process.extractOne(query, [x['name'] for x in choices])
    return [x for x in choices if x['name'] == result[0]][0]


def get_location(search_term):
    from hikster.location.models import Location
    from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

    if "(" in search_term and ")" in search_term:
        terms = str(search_term).rsplit(" ", 1)
        location_id = str(terms[1]).replace("(", "").replace(")", "")
        location = Location.objects_with_eager_loading.values('location_id', 'name', 'shape', 'type') \
            .get(location_id=location_id)
    else:
        try:
            location = Location.objects_with_eager_loading.values('location_id', 'name', 'shape', 'type') \
                .get(name__unaccent=search_term)
        except ObjectDoesNotExist:
            location = Location.objects_with_eager_loading.all() \
                .values('location_id', 'name', 'shape', 'type')
        except MultipleObjectsReturned:
            location = Location.objects_with_eager_loading.all() \
                .values('location_id', 'name', 'shape', 'type')

    return location


def class_for_name(module_name, class_name):
    try:
        # load the module, will raise ImportError if module cannot be loaded
        m = __import__(module_name, globals(), locals(), class_name)
        # get the class, will raise AttributeError if class cannot be found
        c = getattr(m, class_name)
        return c
    except ImportError:
        return None
    except AttributeError:
        return None


def add_to_group(user, class_name, module="."):
    group_class = class_for_name(module, "Group")
    group = group_class.objects.get(name=class_name)
    group.user_set.add(user)


def add_profile(user, class_name, module='.'):
    profile_class = class_for_name(module, class_name)
    profile = profile_class(user=user)
    profile.save()


def save_nested(obj, serializer):
    """
    Takes care of passing nested objects to their respective serializers.
    This is to avoid validation errors as using the expand logic effectively turns relations into
    primary keys instead of nested objects
    :param obj: an dict or a list of dict with properties of the objects to save
    :param serializer: the serializer for the object to save
    :return: the id of the new instance or a list of ids (if many) to save normally
    """

    def save_object(obj, serializer):
        """
        Inner function to save an object using the dict and the serializer from the outer function.
        The goal is to avoid importing two functions
        :param obj: dict or list of dicts from the outer function
        :param serializer: serializer from the outer function
        :return: the object instance
        """
        serializer = serializer(data=obj)
        serializer.is_valid()
        instance = serializer.save()
        return instance

    if type(obj) is list:
        return [save_object(x, serializer).id for x in obj]
    else:
        instance = save_object(obj, serializer)
        return instance


def get_from_dict(d: dict, *k: list) -> object:
    return[d.get(i, None) for i in k]


def send_email(subject=None, message=None, from_email=None, recipient_list=None):
    from smtplib import SMTPException
    from django.core import mail

    try:
        mail.send_mail(subject=subject, message=message, from_email=from_email, recipient_list=[recipient_list])
        print("EMAIL SENT")
    except SMTPException:
        return 0
    return mail

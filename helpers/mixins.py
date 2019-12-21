class IncludeFieldsMixin(object):
    def __init__(self, *args, **kwargs):
        super(IncludeFieldsMixin, self).__init__(*args, **kwargs)

        context = self.context
        if not context:
            return

        request = context.get('request', None)
        if not request:
            return

        fields_to_include = request.query_params.get('include', None)
        if not fields_to_include:
            return

        allowed = set(fields_to_include.split(','))
        existing = set(self.fields.keys())
        for field in existing - allowed:
            self.fields.pop(field)


class ExcludeFieldsMixin(object):
    def __init__(self, *args, **kwargs):
        super(ExcludeFieldsMixin, self).__init__(*args, **kwargs)

        context = self.context
        if not context:
            return

        request = context.get('request', None)
        if not request:
            return

        fields_to_exclude = request.query_params.get('exclude', None)
        if not fields_to_exclude:
            return

        for field_to_exclude in fields_to_exclude.split(','):
            self.fields.pop(field_to_exclude)

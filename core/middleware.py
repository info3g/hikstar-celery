class WidgetMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        return self.get_response(request)

    def process_template_response(self, request, response):
        if "/map-widget/" in request.path:
            params = request.GET
            response.context_data["in_iframe"] = True
            response.context_data["widget_params"] = params.urlencode()
            response.context_data["color"] = params.get("color")

            if params.get("accommodation") in ["0", "false", False]:
                response.context_data["no_accommodation"] = True
        elif response.context_data:
            response.context_data["in_iframe"] = False

        return response

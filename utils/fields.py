from rest_framework.fields import CharField


class ContactField(CharField):
    def to_representation(self, value: str) -> str:
        if "mailto:" in value:
            return (value.split("mailto:"))[1].split("#")[0]
        elif "#" in value and value.count("#") > 1:
            return (value.split("#"))[1].split("#")[0]
        else:
            return value

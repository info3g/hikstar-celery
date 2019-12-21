from typing import Union, Dict, Any

from django.core.mail import send_mail
from rest_framework import serializers


class PeopleDictField(serializers.DictField):
    adults = serializers.IntegerField()
    children = serializers.IntegerField()
    babies = serializers.IntegerField()


class ReservationMailSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email_to = serializers.EmailField()
    email_from = serializers.EmailField()
    phone_number = serializers.CharField()
    reservation_dates = serializers.DictField(child=serializers.DateTimeField())
    people = serializers.DictField(child=serializers.IntegerField())
    message = serializers.CharField(allow_blank=True)

    def save(self):
        email = self._prepare_email()
        send_mail(
            email['subject'],
            email['message'],
            email['from'],
            email['to'],
            fail_silently=False
        )

    def _prepare_email(self) -> Union[None, Dict[str, str]]:
        return {
            'subject': u"Demande de réservation du {date_from} au {date_to}".format(**self._prepare_dates()),
            'message': self._prepare_message(),
            'from': self.validated_data['email_from'],
            'to': [self.validated_data['email_to']],
        }

    def _prepare_message(self) -> str:
        first_name = self.validated_data['first_name']
        last_name = self.validated_data['last_name']
        people = self._prepare_people()
        phone_number = self.validated_data['phone_number']
        message = self.validated_data['message']
        return "{message}\r\n\n{people}\r\n\nVous pouvez nous contacter par courriel ou au {phone_number}.\r\n\nMerci à vous.\r\n\n{first_name} {last_name}" \
            .format(
            message=message,
            people=people,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name
        )

    def _prepare_people(self):
        return "La réservation serait pour {adults} adultes, {children} enfants et {babies} bébés." \
            .format(**self.validated_data["people"])

    def _prepare_dates(self) -> Union[Dict[str, Any]]:
        date_from = self.validated_data['reservation_dates']['from'].date().strftime("%d/%m/%Y")
        date_to = self.validated_data['reservation_dates']['to'].date().strftime("%d/%m/%Y")
        return {
            'date_from': date_from,
            'date_to': date_to
        }

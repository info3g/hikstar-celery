# -*- coding: utf-8 -*-

from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    actions = ['create', 'update', 'partial_update', 'destroy']

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        elif (view.action in self.actions) and type(
                request.user) is not AnonymousUser:
            return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        elif hasattr(request.user, "trailadmin"):
            return request.user.trailadmin in obj.owner.all()


class SimpleIsOwnerOrReadOnly(IsOwnerOrReadOnly):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        elif type(request.user) is not AnonymousUser:
            return True

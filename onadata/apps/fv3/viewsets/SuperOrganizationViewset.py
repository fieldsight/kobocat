from django.db.models import Count
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.views import APIView

from onadata.apps.fieldsight.models import SuperOrganization, Organization
from rest_framework.permissions import IsAuthenticated
from onadata.apps.fsforms.enketo_utils import CsrfExemptSessionAuthentication
from django.contrib.gis.geos import Point
from rest_framework.response import Response
from onadata.apps.fv3.serializers.SuperOrganizationSerializer import OrganizationSerializer
from onadata.apps.fv3.permissions.super_admin import SuperAdminPermission


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = SuperOrganization.objects.all()
    serializer_class = OrganizationSerializer
    authentication_classes = [CsrfExemptSessionAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=False)
            self.object = self.perform_create(serializer)
            self.object.owner = self.request.user
            self.object.date_created = timezone.now()
            self.object.save()
            longitude = request.data.get('longitude', None)
            latitude = request.data.get('latitude', None)
            if latitude and longitude is not None:
                p = Point(round(float(longitude), 6), round(float(latitude), 6),
                          srid=4326)
                self.object.location = p
                self.object.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"test", str(e)})

    def perform_create(self, serializer):
        return serializer.save()


class SuperOrganizationListView(APIView):
    """
    A simple view for list of super organizations.
    """
    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            super_organizations = SuperOrganization.objects.all().annotate(teams=Count('organizations')).\
                values('id', 'name', 'teams')

            return Response(status=status.HTTP_200_OK, data=super_organizations)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'detail': 'You do not have permission to '
                                                                              'perform this action.'})


class ManageTeamsView(APIView):

    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    permission_classes = [IsAuthenticated, SuperAdminPermission]

    def get(self, request, pk, *args,  **kwargs):
        queryset = Organization.objects.all()
        teams = queryset.values('id', 'name')
        selected_teams = queryset.filter(parent_id=pk).values('id', 'name')

        return Response(status=status.HTTP_200_OK, data={'teams': teams, 'selected_teams': selected_teams})

    def post(self, request, pk, format=None):
        team_ids = request.data.get('team_ids', None)

        if team_ids:
            SuperOrganizationListView.objects.filter(id__in=team_ids).update(parent_id=pk)

            return Response(status=status.HTTP_200_OK, data={'detail': 'successfully updated.'})

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'detail': 'team_ids field is required.'})

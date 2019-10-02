from django.db.models import Q, Count

from rest_framework import serializers

from onadata.apps.fieldsight.models import Site
from onadata.apps.fsforms.models import FieldSightXF, Schedule, Stage, FInstance
from django.contrib.humanize.templatetags.humanize import naturaltime


class ViewGeneralsAndSurveyFormSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    title = serializers.SerializerMethodField(read_only=True)
    created_date = serializers.SerializerMethodField(read_only=True)
    last_response = serializers.SerializerMethodField(read_only=True)
    response_count = serializers.SerializerMethodField(read_only=True)
    view_submission_url = serializers.SerializerMethodField(read_only=True)
    download_url = serializers.SerializerMethodField(read_only=True)
    versions_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FieldSightXF
        fields = ('id', 'name', 'title', 'created_date', 'response_count', 'last_response', 'view_submission_url',
                  'download_url', 'versions_url')

    def get_name(self, obj):
        return u"%s" % obj.xf.title

    def get_title(self, obj):
        return u"%s" % obj.xf.id_string

    def get_created_date(self, obj):
        return obj.date_created.strftime("%b %d, %Y at %I:%M %p")

    def get_last_response(self, obj):
        is_project = self.context.get('is_project', False)
        if is_project or obj.project:
            return obj.project_form_instances.order_by('-pk').values_list(
                    'date', flat=True)[:1]

        elif obj.site:
            return obj.site_form_instances.order_by('-pk').values_list(
                    'date', flat=True)[:1]

    def get_response_count(self, obj):
        is_project = self.context.get('is_project', False)
        if is_project or obj.project:
            count = obj.response_count if hasattr(obj, 'response_count') else 0
            return count
        elif obj.site:
            count = obj.site_response_count if hasattr(obj, 'site_response_count') else 0
            return count

    def get_view_submission_url(self, obj):
        is_project = self.context.get('is_project', False)
        if is_project:
            return '/forms/project-submissions/{}'.format(obj.id)
        else:
            return '/forms/site-submissions/{}/{}'.format(obj.id, 149)

    def get_download_url(self, obj):
        if self.get_response_count(obj) > 0:
            is_project = self.context.get('is_project', False)
            if is_project:
                return '/{}/exports/{}/xls/1/{}/0/0/'.format(obj.xf.user.username, obj.xf.id_string, obj.id)
            else:
                return ''

    def get_versions_url(self, obj):
        if obj.has_versions:
            return '/forms/submissions/versions/1/{}'.format(obj.id)


class ViewScheduledFormSerializer(serializers.ModelSerializer):
    form_name = serializers.SerializerMethodField(read_only=True)
    name = serializers.SerializerMethodField(read_only=True)
    title = serializers.SerializerMethodField(read_only=True)
    created_date = serializers.SerializerMethodField(read_only=True)
    last_response = serializers.SerializerMethodField(read_only=True)
    response_count = serializers.SerializerMethodField(read_only=True)
    view_submission_url = serializers.SerializerMethodField(read_only=True)
    download_url = serializers.SerializerMethodField(read_only=True)
    versions_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Schedule
        fields = ('id', 'name', 'form_name', 'title', 'created_date', 'response_count', 'last_response',
                  'view_submission_url', 'download_url', 'versions_url')

    def get_name(self, obj):
        return u"%s" % obj.name

    def get_form_name(self, obj):
        return u"%s" % obj.schedule_forms.xf.title

    def get_title(self, obj):
        return u"%s" % obj.schedule_forms.xf.id_string

    def get_created_date(self, obj):
        return obj.schedule_forms.date_created.strftime("%b %d, %Y at %I:%M %p")

    def get_last_response(self, obj):
        is_project = self.context.get('is_project', False)
        if is_project or obj.project:
            return obj.schedule_forms.project_form_instances.order_by('-pk').values_list(
                    'date', flat=True)[:1]

        elif obj.site:
            return obj.schedule_forms.site_form_instances.order_by('-pk').values_list(
                    'date', flat=True)[:1]

    def get_response_count(self, obj):
        is_project = self.context.get('is_project', False)
        if is_project or obj.project:
            count = obj.response_count if hasattr(obj, 'response_count') else 0
            return count
        elif obj.site:
            count = obj.site_response_count if hasattr(obj, 'site_response_count') else 0
            return count

    def get_view_submission_url(self, obj):
        is_project = self.context.get('is_project', False)
        site = self.context.get('site', False)
        if is_project:
            return '/forms/project-submissions/{}'.format(obj.schedule_forms.id)
        elif site:
            return '/forms/site-submissions/{}/{}'.format(obj.schedule_forms.id, site)

    def get_download_url(self, obj):
        if self.get_response_count(obj) > 0:
            return '/{}/exports/{}/xls/1/{}/0/0/'.format(obj.schedule_forms.xf.user.username, obj.schedule_forms.xf.id_string,
                                                         obj.schedule_forms.id)

    def get_versions_url(self, obj):
        is_project = self.context.get('is_project', False)
        site = self.context.get('site', False)

        if obj.schedule_forms.has_versions:
            if is_project:
                return '/forms/submissions/versions/1/{}'.format(obj.schedule_forms.id)
            elif site:
                return '/forms/submissions/versions/0/{}/{}'.format(obj.schedule_forms.id, site)


class ViewSubStageFormSerializer(serializers.ModelSerializer):
    form_name = serializers.SerializerMethodField()
    response_count = serializers.SerializerMethodField()
    last_response = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField(read_only=True)
    versions_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Stage
        fields = ('id', 'name', 'order', 'form_name', 'response_count', 'last_response', 'download_url', 'versions_url')

    def get_form_name(self, obj):
        return obj.stage_forms.xf.title

    def get_response_count(self, obj):
        is_project = self.context.get('is_project', False)
        if is_project or obj.project:
            count = obj.response_count if hasattr(obj, 'response_count') else 0
            return count
        elif obj.site:
            count = obj.site_response_count if hasattr(obj, 'site_response_count') else 0
            return count

    def get_last_response(self, obj):
        is_project = self.context.get('is_project', False)
        if is_project or obj.project:
            return obj.stage_forms.project_form_instances.order_by('-pk').values_list(
                    'date', flat=True)[:1]

        elif obj.site:
            return obj.stage_forms.site_form_instances.order_by('-pk').values_list(
                    'date', flat=True)[:1]

    def get_download_url(self, obj):
        if self.get_response_count(obj) > 0:
            return '/{}/exports/{}/xls/1/{}/0/0/'.format(obj.stage_forms.xf.user.username, obj.schedule_forms.xf.id_string,
                                                         obj.stage_forms.id)

    def get_versions_url(self, obj):
        is_project = self.context.get('is_project', False)
        site = self.context.get('site', False)

        if obj.stage_forms.has_versions:
            if is_project:
                return '/forms/submissions/versions/1/{}'.format(obj.stage_forms.id)
            elif site:
                return '/forms/submissions/versions/0/{}/{}'.format(obj.stage_forms.id, site)


class ViewStageFormSerializer(serializers.ModelSerializer):
    sub_stages = serializers.SerializerMethodField()

    class Meta:
        model = Stage
        fields = ('id', 'name', 'sub_stages')

    def get_sub_stages(self, obj):
        site_id = self.context.get('site', False)
        is_project = self.context.get('is_project', False)

        if obj.project and is_project:
            is_project = True
            queryset = Stage.objects.filter(stage__isnull=False, stage=obj, project=obj.project)
            queryset = queryset.select_related('stage_forms', 'em').order_by('order', 'date_created').\
                annotate(response_count=Count('stage_forms__project_form_instances'))
            data = ViewSubStageFormSerializer(queryset, many=True, context={'is_project': is_project}).data

            return data

        elif site_id:
            queryset = Stage.objects.filter(stage__isnull=False, stage=obj).order_by('order', 'date_created')
            site = Site.objects.get(id=site_id, is_active=True)
            project_id = site.project.id
            if site.type and site.region:
                queryset = queryset.filter(Q(site__id=site.id, project_stage_id=0)
                                            | Q(project__id=project_id, tags__contains=[site.type_id])
                                            | Q(project__id=project_id, regions__contains=[site.region_id])
                                            )
            elif site.type:
                queryset.filter(Q(site__id=site.id,
                                  project_stage_id=0)
                                | Q(project__id=project_id, tags__contains=[site.type_id])

                                )
            elif site.region:
                queryset = queryset.filter(Q(site__id=site.id,
                                             project_stage_id=0)
                                           | Q(project__id=project_id, regions__contains=[site.region_id])
                                           )
            else:
                queryset = queryset.filter(
                    Q(site__id=site.id, project_stage_id=0)
                    | Q(project__id=project_id))

            queryset = queryset.select_related('stage_forms', 'em').order_by('order', 'date_created').\
                annotate(site_response_count=Count('stage_forms__site_form_instances'))
            data = ViewSubStageFormSerializer(queryset, many=True,  context={'site': site_id}).data
            return data


class ViewSubmissionStatusSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    submitted_by = serializers.CharField(source='submitted_by.username')
    submission_url = serializers.SerializerMethodField()
    profile_url = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = FInstance

        fields = ('id', 'name', 'date', 'submitted_by', 'submission_url', 'profile_url')

    def get_name(self, obj):
        if obj.project_fxf:
            name = obj.project_fxf.xf.title
            return name
        elif obj.site_fxf:
            name = obj.site_fxf.xf.title
            return name

    def get_submission_url(self, obj):
        return '/fieldsight/application/?submission={}#/submission-details'.format(obj.id)

    def get_profile_url(self, obj):
        return '/users/profile/{}/'.format(obj.submitted_by.id)

    def get_date(self, obj):
        return naturaltime(obj.date)


class FormSubmissionSerializer(serializers.ModelSerializer):
    submitted_by = serializers.CharField(source='submitted_by.get_full_name')
    profile_url = serializers.SerializerMethodField()
    site_name = serializers.CharField(source='site.name')
    site_identifier = serializers.CharField(source='site.identifier')

    class Meta:
        model = FInstance
        fields = ('id', 'date', 'submitted_by', 'profile_url', 'site_name', 'site_identifier')

    def get_profile_url(self, obj):
        return '/users/profile/{}/'.format(obj.submitted_by.id)

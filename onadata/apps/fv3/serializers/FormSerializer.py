from rest_framework import serializers

from onadata.apps.logger.models import XForm

from onadata.apps.fsforms.models import Asset, FieldSightXF

from onadata.apps.fieldsight.models import Project, Organization


from django.conf import settings
from django.contrib.auth.models import User
from datetime import datetime


class XFormSerializer(serializers.ModelSerializer):
    date_created = serializers.SerializerMethodField()
    date_modified = serializers.SerializerMethodField()
    edit_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    replace_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    media_url = serializers.SerializerMethodField()
    share_users_url = serializers.SerializerMethodField()
    share_project_url = serializers.SerializerMethodField()
    share_team_url = serializers.SerializerMethodField()
    share_global_url = serializers.SerializerMethodField()
    add_language_url = serializers.SerializerMethodField()
    clone_form_url = serializers.SerializerMethodField()
    delete_url = serializers.SerializerMethodField()
    shareable_users_url = serializers.SerializerMethodField()
    shareable_teams_url = serializers.SerializerMethodField()

    class Meta:
        model = XForm
        fields = ('id_string','title', 'edit_url', 'preview_url', 'replace_url',
                  'download_url', 'media_url', 'date_created', 'date_modified', 'share_users_url',
                  'share_project_url', 'share_team_url', 'share_global_url', 'add_language_url',
                  'clone_form_url', 'delete_url', 'shareable_users_url', 'shareable_teams_url')

    def get_date_created(self, obj):
        date_created = obj.date_created
        date_created = datetime.strftime(date_created, "%Y-%m-%d")
        return date_created

    def get_date_modified(self, obj):
        date_modified = obj.date_modified
        date_modified = datetime.strftime(date_modified, "%Y-%m-%d")
        return date_modified

    def get_edit_url(self, obj):
        return "{}#forms/{}/edit/".format(settings.KPI_URL, obj.id_string)

    def get_preview_url(self, obj):
        return "{}/forms/preview/{}/".format(settings.KOBOCAT_URL, obj.id_string)

    def get_replace_url(self, obj):
        return "{}{}/".format(settings.KPI_URL,"import")

    def get_download_url(self, obj):
        return "{}{}.{}".format(settings.KPI_ASSET_URL, obj.id_string, "xls")

    def get_media_url(self, obj):
        return "{}/{}/forms/{}/form_settings".format(settings.KOBOCAT_URL, obj.user.username, obj.id_string)

    def get_share_users_url(self, obj):
        return "{}/fv3/api/share/".format(settings.KOBOCAT_URL)

    def get_share_project_url(self, obj):
        return "{}/fv3/api/share/project/".format(settings.KOBOCAT_URL)

    def get_share_team_url(self, obj):
        return "{}/fv3/api/share/team/".format(settings.KOBOCAT_URL)

    def get_share_global_url(self, obj):
        return "{}/fv3/api/share/global/".format(settings.KOBOCAT_URL)

    def get_add_language_url(self, obj):
        return "{}/fv3/api/add-language/".format(settings.KOBOCAT_URL)

    def get_clone_form_url(self, obj):
        return "{}/fv3/api/clone/".format(settings.KOBOCAT_URL)

    def get_delete_url(self, obj):
        return "{}/fv3/api/form/delete/".format(settings.KOBOCAT_URL)

    def get_shareable_users_url(self, obj):
        return "{}/fv3/api/form/users/".format(settings.KOBOCAT_URL)

    def get_shareable_teams_url(self, obj):
        return "{}/fv3/api/form/teams/".format(settings.KOBOCAT_URL)


class ShareUserListSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile_picture')

    def get_profile_picture(self, obj):
        try:
            image_url = obj.user_profile.profile_picture.url
            return image_url
        except:
            return ''


class ShareTeamListSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ('id', 'name', 'logo')

    def get_logo(self, obj):
        return obj.logo.url


class ProjectFormSerializer(serializers.ModelSerializer):
    forms = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'name', 'forms')

    def get_forms(self, obj):
        xf = XForm.objects.filter(field_sight_form__project=obj).distinct()
        serializer = XFormSerializer(xf, many=True)
        return serializer.data


class ShareFormSerializer(serializers.Serializer):
    id_string = serializers.CharField()
    users = serializers.ListField(child=serializers.IntegerField())


class ShareProjectFormSerializer(serializers.Serializer):
    id_string = serializers.CharField()
    project = serializers.IntegerField()


class ShareTeamFormSerializer(serializers.Serializer):
    id_string = serializers.CharField()
    team = serializers.IntegerField()


class ShareGlobalFormSerializer(serializers.Serializer):
    id_string = serializers.CharField()


class AddLanguageSerializer(serializers.Serializer):
    id_string = serializers.CharField()
    language = serializers.CharField()
    code = serializers.CharField()


class CloneFormSerializer(serializers.Serializer):
    id_string = serializers.CharField()
    project = serializers.IntegerField()


class MyFormDeleteSerializer(serializers.Serializer):
    id_string = serializers.CharField()


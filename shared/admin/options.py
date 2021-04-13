from shared.admin.filters import UserDetailsFilter
from django.contrib import admin
from authentication.models import User
from django.contrib import messages
from import_export.admin import ImportExportModelAdmin

class UserDetailsAdmin(ImportExportModelAdmin):
    user_field_name = 'user'
    
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

    def get_list_filter(self, request):
        super_lf = super().get_list_filter(request)
        lf = (
            UserDetailsFilter,
            *super_lf
        )
        return lf

    def get_user_field_name(self):
        model = self.model
        if not hasattr(model, self.user_field_name):
            opts = self.opts
            for field in opts.fields:
                rel = getattr(field, 'remote_field', None)
                if rel and rel.model == User:
                    self.user_field_name = str(field).split('.')[-1]
        return self.user_field_name

    def get_autocomplete_fields(self, request):
        super_af = super().get_autocomplete_fields(request)
        af = (
            self.get_user_field_name(),
            *super_af
        )
        return af

class DropdownAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    is_translated = False

    def get_search_fields(self, request):
        super_sf = super().get_search_fields(request)
        if self.is_translated:
            sf = (
                'name_hi',
                *super_sf
            )
            return sf
        return super_sf

class HomepageDetailsAdmin(admin.ModelAdmin):
    help_texts = {}
    min_obj_cnt = 1
    select_related_fields = []
    list_display_links = ('__str__',)
    has_admin_ordering = True

    def get_list_filter(self, request):
        super_lf = super().get_list_filter(request)
        lf = (
            'is_disabled',
            *super_lf
        )
        return lf

    def get_list_display(self, request):
        super_ld = super().get_list_display(request)
        super_ld = [*super_ld,]
        rm_fields = ['__str__', 'is_disabled', '_reorder',]
        for f in rm_fields:
            if f in super_ld:
                super_ld.remove(f)
        ld = [
            '__str__',
            *super_ld,
            'is_disabled',
        ]
        if self.has_admin_ordering:
            ld.append('_reorder')
        return tuple(ld)

    def can_delete_obj(self, request, qs_list):
        min_cnt = self.min_obj_cnt
        if min_cnt <= 0:
            return True
        model = self.model
        cnt = model.objects.filter(is_disabled = False).exclude(id__in = qs_list).count()
        can_del = cnt >= min_cnt
        if not can_del:
            model_name = self.model.__name__.lower()
            messages.error(request, 'Error deleting {}.'.format(model_name))
            messages.error(request, 'There must be atleast {cnt} {name}'.format(name = model_name, cnt = min_cnt))
        return can_del

    def delete_model(self, request, obj):
        can_del = self.can_delete_obj(request, [obj.id])
        if can_del:
            obj.delete()

    def delete_queryset(self, request, queryset):
        can_del = self.can_delete_obj(request, list(queryset.values_list('id', flat=True)))
        if can_del:
            queryset.delete()

    def disable_objects(self, request, queryset):
        can_del = self.can_delete_obj(request, list(queryset.values_list('id', flat=True)))
        if can_del:
            queryset.update(is_disabled = True)

    def enable_objects(self, request, queryset):
        queryset.update(is_disabled = False)

    def _get_base_actions(self):
        super_actions = super()._get_base_actions()
        actions = [*super_actions]
        for action in ['disable_objects', 'enable_objects',]:
            actions.append(self.get_action(action))
        return actions

    def get_form(self, request, obj=None, **kwargs):
        if self.help_texts:
            help_texts = kwargs.get('help_texts', {})
            help_texts.update(self.help_texts)
            kwargs.update({'help_texts': help_texts})
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        return qs


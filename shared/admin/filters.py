from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.contrib.admin.options import IncorrectLookupParameters
from authentication.models import User

class InputFilter(admin.SimpleListFilter):
    template = 'admin/input_filter.html'

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice

class CharFieldFilter(InputFilter):
    field_name = None

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        if not self.field_name:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify a 'field_name'."
                % self.__class__.__name__
            )

    def queryset(self, request, queryset):
        field_value = self.value()
        if field_value is None:
            return queryset
        if field_value:
            filter_data = {
                self.field_name: field_value,
            }
            try:
                return queryset.filter(**filter_data)
            except (ValueError, ValidationError) as e:
                # Fields may raise a ValueError or ValidationError when converting
                # the parameters to the correct type.
                raise IncorrectLookupParameters(e)
        return queryset.model.objects.none()

class RelatedFieldFilter(InputFilter):
    model_name = None
    related_name = None
    fields_list = None

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        if not self.fields_list:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify a 'fields_list'."
                % self.__class__.__name__
            )
        if self.model_name:
            self.model_name = self.model_name.replace(' ', '').lower()
            self.related_name = model._meta.get_field(self.model_name).related_name
            if not self.related_name:
                self.related_name = self.model_name + '_set'

    def queryset(self, request, queryset):
        field_value = self.value()
        if field_value is None:
            return queryset
        res_queryset = queryset.model.objects.none()
        if field_value:
            for field in self.fields_list:
                field_name = self.related_name + '__' + field + '__icontains'
                filter_data = {
                    field_name: field_value,
                }
                try:
                    qs = queryset.filter(**filter_data)
                    res_queryset = res_queryset | qs
                except (ValueError, ValidationError) as e:
                    pass
        return res_queryset.distinct()


class UserDetailsFilter(RelatedFieldFilter):
    parameter_name = 'user'
    title = 'User'
    related_name = 'user'
    fields_list = ('username', 'first_name', 'last_name',)

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)
        if not hasattr(model, self.related_name):
            opts = model._meta
            for field in opts.fields:
                rel = getattr(field, 'remote_field', None)
                if rel and rel.model == User:
                    self.related_name = str(field).split('.')[-1]


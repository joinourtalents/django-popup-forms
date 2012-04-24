
from django.utils.importlib import import_module
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def popup_forms(request):
    """Puts all popup forms to 'popup_forms' context variable."""

    popup_forms = {}
    for popup_form in settings.POPUP_FORMS:
        module_name, sep, form_name = popup_form.rpartition('.')
        try:
            mod = import_module(module_name)
        except ImportError, e:
            raise ImproperlyConfigured('Error importing popup form '
                    'from module {0}: "{1}"'.format(module_name, e))
        try:
            popup_forms[form_name] = getattr(mod, form_name)
        except AttributeError:
            raise ImproperlyConfigured('Module "{0}" does not define'
                    ' a "{1}" form class'.format(module_name, form_name))
    return {'popup_forms': popup_forms}

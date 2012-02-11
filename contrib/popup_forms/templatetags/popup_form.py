from copy import copy

from django import template

from candidate.models import CandidateProfile
from recruiter.models import CompanyProfile
from django.template.context import RequestContext

register = template.Library()


def do_popup_form(parser, token):
    """Renders form using `popup_forms/base.html` template.

    Tries to re-populate the form with data, stored in session
    by `popup_forms.decorators.popup_form` decorator.

    Session keys::

      popup_form      Popup form instance, put by the
                      `custom.decorators.popup_form` decorator,
                      which should be re-populated -- for example,
                      in case of validation errors.
                      If defined, only one form is re-populated
                      (with action==popup_form.action), which is
                      not hidden. Other popup forms are not populated
                      in this case in whole template.

    """

    try:
        contents_split = token.split_contents()
        template_name = "'popup_forms/base.html'"
        if len(contents_split) == 4:
            tag_name, popup_id, form_class, form_action = contents_split
        else:
            (tag_name, popup_id, form_class,
             form_action, template_name) = contents_split
    except ValueError:
        raise template.TemplateSyntaxError('{0} tag requires '
                'at least three arguments: '
                'popup_id, form_class and action'
                .format(token.contents.split()[0]))
    return PopupFormNode(popup_id, form_class, form_action, template_name)

register.tag('popup_form', do_popup_form)


class PopupFormNode(template.Node):
    def __init__(self, popup_id, form_class, form_action, template_name):
        self.popup_id = template.Variable(popup_id)
        self.form_class = template.Variable(form_class)
        self.form_action = template.Variable(form_action)
        self.template_name = template.Variable(template_name)

    def render(self, context):

        # Resolve variables
        popup_id = self.popup_id.resolve(context)
        form_class = self.form_class.resolve(context)
        form_action = self.form_action.resolve(context)
        template_name = self.template_name.resolve(context)

        # Django tries to call callables, so we extract
        # form class from the form instance
        if isinstance(form_class, type):
            form_instance = form_class()
        else:
            form_instance = form_class
            form_class = form_instance.__class__

        # Try to get popup_form from session
        # (emulate response to POST request for popup form)
        request = context['request']
        if 'popup_form' in request.session:
            action, data = request.session['popup_form']

            # A page could have many popup forms,
            # with different actions
            if action == form_action:
                del request.session['popup_form']
                form_instance = form_class(data)
                # Try to validate form, to show errors
                form_instance.is_valid()
            else:
                # If popup_form exists in session, but
                # does not correspond to current form,
                # the current form just not rendered,
                # because only one popup form could be visible
                return ''

        # Render popup form, using template
        tpl = template.loader.get_template(template_name)
        context_vars = {'popup_id': popup_id,
                        'form': form_instance,
                        'action': form_action}
        context = copy(context)
        context.update(context_vars)
        return tpl.render(RequestContext(request, context))


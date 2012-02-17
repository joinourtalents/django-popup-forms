from copy import copy

from django import template

from candidate.models import CandidateProfile
from recruiter.models import CompanyProfile
from django.template.context import RequestContext

register = template.Library()


def do_popup_form(parser, token):
    """Renders form, and link to display it.

    Tries to re-populate the form with data, stored in session
    by `popup_forms.decorators.popup_form` decorator.

    Session keys::

      popup_form      Tuple: (action, data, errors), put by the
                      `custom.decorators.popup_form`, to
                      re-populate form. First popup_form,
                      matching the specified action url,
                      is re-populated with data, and made
                      visible.

      popup_form[0]   Action url for the form to be re-populated

      popup_form[1]   Form data dictionary, used to create
                      the bound form instance. In case it's
                      `None`, unbound form instance is created.

      popup_form[2]   Form errors to be assigned to created
                      form instance.

    Usage::

        {% popup_form 'id_suffix' form_class form_action_url template %}

    , where::

        :id_suffix:         Suffix to be appended to ID of form and link.
                            Should be unique within the page.
        :form_class:        Form class to be used to render the popup form.
        :form_action_url:   `action` attribute for the <form>
        :template:          Template used to render link and form.
        :instance:          For ModelForms only -- primary key or instance
                            of the model to be used to create the form.

    """

    try:
        contents_split = token.split_contents()
        instance = None
        if len(contents_split) == 5:
            (tag_name, popup_id, form_class,
             form_action, template_name) = contents_split
        else:
            (tag_name, popup_id, form_class,
             form_action, template_name, instance) = contents_split
    except ValueError:
        raise template.TemplateSyntaxError('{0} tag requires '
                'at least four arguments: '
                '"popup_id", "form_class", "action" and "template". '
                'Fifth argument "instance" is optional.'
                .format(token.contents.split()[0]))
    return PopupFormNode(popup_id, form_class,
                         form_action, template_name, instance)

register.tag('popup_form', do_popup_form)


class PopupFormNode(template.Node):
    def __init__(self, popup_id, form_class, form_action,
                 template_name, instance):
        self.popup_id = template.Variable(popup_id)
        self.form_class = template.Variable(form_class)
        self.form_action = template.Variable(form_action)
        self.template_name = template.Variable(template_name)
        self.instance = template.Variable(instance) if instance else None

    def render(self, context):

        # Resolve variables
        popup_id = self.popup_id.resolve(context)
        form_class = self.form_class.resolve(context)
        form_action = self.form_action.resolve(context)
        template_name = self.template_name.resolve(context)
        instance = self.instance.resolve(context) if self.instance else None

        # Django tries to call callables, so we extract
        # form class from the form instance
        if isinstance(form_class, type):
            form_instance = form_class()
        else:
            form_instance = form_class
            form_class = form_instance.__class__

        # Try to get popup_form from session
        # (emulate response to POST request for popup form)
        hide_form = True  # Hide form by default, unless form is in session
        request = context['request']
        if 'popup_form' in request.session:
            action, data, errors = request.session['popup_form']

            # A page could have many popup forms,
            # with different actions
            if action == form_action:
                del request.session['popup_form']

                # Instantiate the form
                args, kwargs = [], {}
                if data is not None:
                    args.append(data)
                if (instance is not None and hasattr(form_class, '_meta')
                        and hasattr (form_class._meta, 'model')):
                    # For model form - try to find the instance
                    model_class = form_class._meta.model
                    if not isinstance(instance, model_class):
                        instance = model_class.objects.get(pk=instance)
                    kwargs['instance'] = instance
                form_instance = form_class(*args, **kwargs)

                # If there are errors, show them
                if errors:
                    form_instance._errors = errors

                # Mark the form as non-hidden
                hide_form = False

        # Render popup form, using template
        tpl = template.loader.get_template(template_name)
        context_vars = {'popup_id': popup_id,
                        'form': form_instance,
                        'action': form_action,
                        'hide_popup_form': hide_form}
        context = copy(context)
        context.update(context_vars)
        return tpl.render(RequestContext(request, context))


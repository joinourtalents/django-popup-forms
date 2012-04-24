import re
from copy import copy

from django import template
from django.template.context import RequestContext

register = template.Library()


class TokenVarExtractor(object):
    """Extracts variables from split content of the token.

    Used to extract both positional and keyword arguments.

    :param token: The token object, passed to template function

    """

    def __init__(self, token):
        self.token_content = token.split_contents()
        self.tag_name = self.token_content.pop(0)

    @staticmethod
    def split(item):
        """Split key and value. Return tuple (key, value).

        >>> TokenVarExtractor.split('asdf')
        (None, "'asdf'")
        >>> TokenVarExtractor.split('myname="asdf"')
        ("myname", "'asdf'")
        >>> TokenVarExtractor.split('myname=asdf')
        ("myname", "asdf")
        >>> TokenVarExtractor.split('myna-me=asdf')
        (None, "myna-me=asdf")

        """
        key, sep, value = item.rpartition('=')
        if key:
            key = key.strip()
            if re.match('\w+', key):
                return key, value.strip()
        return None, item

    def has_more(self):
        """Checks, if there are more args/kwargs available"""
        return bool(self.token_content)

    def pop(self, key=None):
        """Extract either positional or keyword argument.

        If keyword argument is found, it is extracted and removed
        from the token content.

        If keyword argument is not found, and there still are positional
        arguments, the first positional argument is extracted and
        removed from token content.

        If keyword argument is not found, and there are no positional
        arguments anymore, exception is raised.

        If key is not specified, first positional argument is returned
        and removed. If there is no positional argument, exception is raised.

        """

        if not self.token_content:
            raise template.TemplateSyntaxError(
                u'Template tag argument is missing: {0}'.format(key))

        # If key is specified:
        if key:
            for item in self.token_content:
                ret_key, ret_value = self.split(item)
                if ret_key == key:
                    self.token_content.remove(item)
                    return ret_value

        # If key is not specified, or not found in kwargs
        item = self.token_content.pop(0)
        ret_key, ret_value = self.split(item)
        if ret_key:
            if key:
                raise template.TemplateSyntaxError(
                    u'Keyword argument not found: {0}'.format(key))
            else:
                raise template.TemplateSyntaxError(
                    u'Positional argument expected; keyword found: {0}'
                    .format(item))
        return item

    def kwargs(self):
        """Returns remaining keyword arguments"""
        ret = {}
        for item in self.token_content:
            key, value = self.split(item)
            if not key:
                raise template.TemplateSyntaxError(
                        'Unexpected positional argument: {0}'.format(item))
            ret[key] = value
        return ret


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

        {% popup_form 'id_suffix' form_class form_action template %}
        {% popup_form id_suffix=... form_class=... form_action=... template=... instance=... %}
        {% popup_form 'id_suffix' form_class form_action template kwarg1=... kwarg2=... %}

    , where::

        :id_suffix:         Suffix to be appended to ID of form and link.
                            Should be unique within the page.
        :form_class:        Form class to be used to render the popup form.
        :form_action:       `action` attribute for the <form>
        :template:          Template used to render link and form.
        :kwargs:            Optionally, any number of keyword arguments could be used,
                            that are passed to form constructor as **kwargs

    """

    try:
        extractor = TokenVarExtractor(token)
        popup_id = extractor.pop('id_suffix')
        form_class = extractor.pop('form_class')
        form_action = extractor.pop('form_action')
        template_name = extractor.pop('template')

    except ValueError:
        raise template.TemplateSyntaxError('{0} tag requires '
                'at least four arguments: '
                '"popup_id", "form_class", "action" and "template". '
                .format(token.contents.split()[0]))
    return PopupFormNode(popup_id, form_class,
                         form_action, template_name,
                         **extractor.kwargs())

register.tag('popup_form', do_popup_form)


class PopupFormNode(template.Node):
    def __init__(self, popup_id, form_class, form_action,
                 template_name, **kwargs):
        self.popup_id = template.Variable(popup_id)
        self.form_class = template.Variable(form_class)
        self.form_action = template.Variable(form_action)
        self.template_name = template.Variable(template_name)

        # Store kwargs
        self.kwargs = {}
        for key, value in kwargs.iteritems():
            self.kwargs[key] = template.Variable(value)

    def render(self, context):

        # Resolve variables
        popup_id = self.popup_id.resolve(context)
        form_class = self.form_class.resolve(context)
        form_action = self.form_action.resolve(context)
        template_name = self.template_name.resolve(context)

        # Resolve kwargs
        kwargs = {}
        for key, value in self.kwargs.iteritems():
            kwargs[key] = value.resolve(context)

        # Django tries to call callables, so we extract
        # form class from the form instance
        if not isinstance(form_class, type):
            form_class = form_class.__class__
        form_instance = form_class(**kwargs)

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
                args = []
                if data is not None:
                    args.append(data)
                form_instance = form_class(*args, **kwargs)

                # If there are errors, show them
                if errors:
                    form_instance._errors = errors

                # Mark the form as non-hidden
                hide_form = False

        # Render popup form, using template
        tpl = template.loader.get_template(template_name)
        context_vars = {'POPUP_FORM_id': popup_id,
                        'POPUP_FORM_form': form_instance,
                        'POPUP_FORM_action': form_action,
                        'POPUP_FORM_hide': hide_form}
        context = copy(context)
        context.update(context_vars)
        return tpl.render(RequestContext(request, context))

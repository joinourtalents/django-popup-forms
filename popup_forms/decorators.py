"""Decorators for popup form processing views"""

from functools import wraps
from django.http import Http404, HttpResponseRedirect


def handler(func):
    """Decorator for popup form handling view.

    Re-populate submitted popup form with error on referrer's page.

    Popup forms (for sending messages, inviting to events, etc.) are
    originally rendered hidden in the template, from which they should
    be sent. This decorator wraps a view processing submission
    of popup form.

    The popup handling view should return one of following objects::

      * popup_forms.CloseFormResponse
      * popup_forms.OpenFormResponse

    In case of returning `CloseFormResponse` the browser is redirected by
    default to the same page, without populating form. In case of returning
    `OpenFormResponse` browser by default is redirected to the same page,
    and the form is re-populated. This decorator puts the form with
    errors to session, and redirects
    back to original view, from where form was submitted. Then
    popup form is re-populated, showing all errors.

    Both `OpenForm` and `CloseForm` have optional `redirect_to`
    argument, specifying the URL to redirect instead of default one.

    .. IMPORTANT::
        * View should not render anything (i.e. return `HttpResponse`).
        * If form validation failed, view should return
          `OpenFormResponse` passing form as only argument::

              if not form.is_valid():
                  return OpenFormResponse(form)

    """

    @wraps(func)
    def wrapper(request, *args, **kwargs):

        # Delete old popup form from session
        if 'popup_form' in request.session:
            del request.session['popup_form']

        # Process the form and redirect to the next URL
        response = func(request, *args, **kwargs)
        if isinstance(response, HttpResponseRedirect):
            return response

        # The view should NOT populate form itself!
        if request.method == 'POST':
            raise ValueError('View for processing popup form populates it!')
        else:
            raise Http404

    return wrapper


def show_popup_form(action, check_function=None):
    """Explicitly shows popup when rendering template in decorated view.

    Works only in case no popup form is defined to be shown
    (i.e. there is no request.session['popup_form']).

    :action: Action URL for which popup should be made visible

    :check_function: Callable, returning boolean value, to determine
    whether popup should be shown or not. If `None`, the popup
    is shown implicitly. Should have the same signature as
    decorated view function: ``func(request, *args, **kwargs)``

    """
    def make_wrapper(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if ('popup_form' not in request.session
               and (not check_function
                    or check_function(request, *args, **kwargs))):
                request.session['popup_form'] = (action, None, None)
            return func(request, *args, **kwargs)
        return wrapper
    return make_wrapper


def popup_if_session_var(action, session_key):
    """Shows popup form for specified view, if the key found in session."""
    # See `popup_forms.decorators.show_popup_form` decorator for more info.
    def _check_function(request, *args, **kwargs):
        return (request.user.is_authenticated()
                and session_key in request.GET   # for testing purposes
                or session_key in request.session)
    return show_popup_form(action, _check_function)

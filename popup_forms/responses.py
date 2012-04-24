"""Popup-form-specific HttpResponse classes"""
from django.http import HttpResponseRedirect


class OpenFormResponse(HttpResponseRedirect):
    """Redirects back to the referer, re-opening the popup form"""

    def __init__(self, request, form=None, redirect_to=None):
        if form:
            request.session['popup_form'] = (request.path,
                                             form.data, form.errors)
        else:
            request.session['popup_form'] = request.path, None, None

        if redirect_to is None:
            redirect_to = request.META.get('HTTP_REFERER', '/')

        return super(OpenFormResponse, self).__init__(redirect_to)


class CloseFormResponse(HttpResponseRedirect):
    """Redirects back to the referer, closing the popup form"""

    def __init__(self, request, redirect_to=None):

        # Delete old popup form from session
        if 'popup_form' in request.session:
            del request.session['popup_form']

        if redirect_to is None:
            redirect_to = request.META.get('HTTP_REFERER', '/')
        return super(CloseFormResponse, self).__init__(redirect_to)

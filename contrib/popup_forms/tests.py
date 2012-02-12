"""Unittests for Popup Forms functionality"""

from django import test, forms
from django.conf.urls import patterns, url
from django.http import HttpResponse
from popup_forms.decorators import popup_form, PopupFormValidationError
from django.shortcuts import render, redirect
from django.test.utils import override_settings


class PopupForm(forms.Form):
    name = forms.CharField(max_length=10)
    email = forms.EmailField(max_length=20)

    def save(self):
        return '{name}, {email}'.format(**self.cleaned_data)


def index(request):
    return HttpResponse('Hello, World!')


def render_form(request):
    return render(request, 'popup_forms_test/page.html')


@popup_form
def process_form(request):
    if request.method == 'POST':
        form = PopupForm(request.POST)
        if not form.is_valid():
            raise PopupFormValidationError(form)
        request.session['stored_data'] = form.save()
        return redirect('success')
    return redirect('render_form')


def success(request):
    return HttpResponse(request.session.pop('stored_data', 'No data'))


urlpatterns = patterns('',
    url(r'^$', index, name='index'),
    url(r'^render_form/$', render_form, name='render_form'),
    url(r'^process_form/$', process_form, name='process_form'),
    url(r'^success/$', success, name='success'),
)

@override_settings(POPUP_FORMS = ('popup_forms.tests.PopupForm',))
class TestPopupForm(test.TestCase):
    """Unit-testing popup forms"""

    urls = 'popup_forms.tests'

    def test_render_form(self):
        """Form should be rendered by `popup_form` template tag"""
        response = self.client.get('/render_form/')
        print response
        self.assertContains(response, '<form method="post" action="/process_form/">')
        self.assertContains(response, '<a href="/process_form/" id="popup_link1"')
        self.assertContains(response, 'style="display:none"')
        self.assertContains(response, '<input id="id_name" type="text" '
                            'name="name" maxlength="10" />')
        self.assertContains(response, '<input id="id_email" type="text" '
                            'name="email" maxlength="20" />')


    def test_submit_form(self):
        """Form processing view should redirect to success page after submit"""
        response = self.client.post('/process_form/',
                    data={'name': 'David', 'email': 'avsd05@gmail.com'},
                    HTTP_REFERER='/render_form/', follow=True)
        self.assertRedirects(response, '/success/')
        print response
        self.assertContains(response, 'David, avsd05@gmail.com')

    def test_error_in_form(self):
        """Form should be re-populated on the same page with errors highlighted"""
        response = self.client.post('/process_form/',
                    data={'name': 'David', 'email': 'wrongemail'},
                    HTTP_REFERER='/render_form/', follow=True)
        self.assertRedirects(response, '/render_form/')
        self.assertNotContains(response, 'style="display:none"')
        self.assertContains(response, 'Enter a valid e-mail address.')
        self.assertContains(response, '<input id="id_name" type="text" '
                            'name="name" value="David" maxlength="10" />')
        self.assertContains(response, '<input id="id_email" type="text" '
                            'name="email" value="wrongemail" maxlength="20" />')

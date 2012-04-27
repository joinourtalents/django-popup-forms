================================
Popup forms framework for Django
================================

Problem
-------

* To have easy way to show popup window, holding any form,
  from any page of the website (examples: send message from user
  profile or from list of profiles; apply/withdraw to pool from
  list of companies, etc.)

* This popup window should be pre-loaded, i.e. there should not
  be HTTP request to server in order to open popup window

* In case form error occurs (some fields are missing,
  email format is wrong, etc.) the same form should be re-populated
  in the same page, indicating errors

* After form is submitted, user should be redirected
  to either the same, or specified page

Solution
--------

The solution consists of 4 components:

* Template tag, rendering popup form and link for opening it::

      {% popup_form 'id1' popup_forms.ApplyForm '/talent/apply/6/' 'popup_forms/apply_to_pool.html' %}
      {% popup_form 'id2' popup_forms.SomeModelForm '/talent/apply/6/' 'popup_forms/apply_to_pool.html' kwarg1=... kwarg2=... %}

* Decorator for view function, that is processing popup form submission,
  and exception to handle form errors::

      import popup_forms

      @popup_forms.handler
      def form_view(request):
          if request.method == 'POST':
              form = ApplyForm(request.post)
              if not form.is_valid():
                  return popup_forms.OpenFormResponse(request, form)
              # ...
              # ... FORM PROCESSING GOES HERE ...
              # ...
              return popup_forms.CloseFormResponse(request)
          else:
              return redirect('failure_url')
              # or raise Http404
              # or just popup_forms.CloseFormResponse(request)

* Template to render the form, derived from popup_forms/base.html
* (optional) context processor (popup_forms.context_processors.popup_forms),
  that puts all PopUp form classes to context, in order not to pass it each time in view:

    - in settings::

        POPUP_FORMS = ('messages.forms.WriteMessageForm',
                       'talentbutton.forms.ApplyForm',
                       'talentbutton.forms.ConfirmForm',)

    - in template it could be accessed::

        {{ popup_forms.WriteMessageForm }}, etc. 

* Decorator to conditionally display popup form on page load
  (for example, to fill in some missing information after registration/login)::

      @show_popup_form('/account/register/details/',
                       lambda request: 'register-details' in request.session)
      def some_my_view(request):
          ...


Use case is following:

* Template tags renders the form, together with link::

      <a href="..." onclick="open the form">Link Title</a>
      <div class="hidden_form">
          <form>...</form>
      </div>

* When user clicks on link, the form, already pre-loaded in template, just makes visible
* User fills form, and submits it. POST request goes to form processing URL
* If form is valid, it is processed, handler returns `CloseFormResponse`
  to close the popup form, and user is redirected to success url
  (which by default is the referrer page where popup form was rendered)
* If form contains errors, handler returns `OpenFormResponse`,
  it is handled by decorator, which stores form data AND ERROR DATA
  in session, and redirects back to referring view
* The ``{% popup_form %}`` tag then finds data, stored by decorator,
  and re-populates form making it VISIBLE (not hidden) - user
  sees the same form, with errors

Conditions
----------

There is no separate template to be rendered by form processing view.
That's why form processing view should not render anything: it just porcesses forms,
and makes redirects. If the view renders something, the decorator raises exception.

Disadvantages
-------------

* If there are many links in the page, for each link a separate form is rendered hiddenly.
  However, HTML of the form does not take much space (less than 1000 characters)

* Right now we have problem to scroll page to the same position
  after re-populating form with errors, but it can be resolved


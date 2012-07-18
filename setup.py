from setuptools import setup

try:
    long_description = open('README.rst').read()
except IOError:
    long_description = ''

setup(
    name='django-popup-forms',
    version='1.0.3',
    description='Django pop-up forms framework.',
    long_description=long_description,
    author='Social TRM Ltd',
    author_email='david@socialtrm.com',
    url='http://github.com/joinourtalents/django-popup-forms',
    keywords = "django",
    packages=['popup_forms', 'popup_forms.templatetags'],
    include_package_data=True,
    package_data={
        'popup_forms': ['templates/popup_forms/*.html',
                        'templates/popup_forms_test/*.html',
                        'static/css/*.css',
                        'static/js/*.js',]
    },
    zip_safe=False,
    license='BSD License',
    platforms = ['any'],
)

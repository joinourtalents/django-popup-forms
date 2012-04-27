from setuptools import setup

try:
    long_description = open('README.rst').read()
except IOError:
    long_description = ''

setup(
    name='django-popup-forms',
    version='1.0.1',
    description='Django pop-up forms framework.',
    long_description=long_description,
    author='Social TRM Ltd',
    author_email='david@socialtrm.com',
    url='http://github.com/joinourtalents/django-popup-forms',
    keywords = "django",
    packages=['popup_forms'],
    include_package_data=True,
    zip_safe=False,
    license='BSD License',
    platforms = ['any'],
)

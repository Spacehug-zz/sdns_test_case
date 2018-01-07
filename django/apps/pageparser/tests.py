from django.test import TestCase
from django.urls import reverse

from .forms import URLSubmitForm
from .helpers import absolutize_url, process_page, reinforce_text, schemeful_domain, sterilize_page

from django.test.runner import DiscoverRunner


class DatabaselessTestRunner(DiscoverRunner):
    """
    A test suite runner that does not set up and tear down a database
    """

    def setup_databases(self):
        """
        Overrides DjangoTestSuiteRunner
        """
        pass

    def teardown_databases(self, *args):
        """
        Overrides DjangoTestSuiteRunner
        """
        pass


class FormTest(TestCase):

    def test_valid_form(self):
        sample_form_data= [
            {
                'target_url': 'https://google.com'
            },
            {
                'target_url': 'http://ерц69.рф'
            },
            {
                'target_url': 'http://ru.wikipedia.org/'
            }
        ]
        for data in sample_form_data:
            form = URLSubmitForm(data=data)
            self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        sample_form_data= [
            {
                'target_url': 'a:b.c:d'
            }
        ]
        for data in sample_form_data:
            form = URLSubmitForm(data=data)
            self.assertFalse(form.is_valid())


class HelpersFunctionsTest(TestCase):

    def test_absolutize_url(self):
        sample_data = [
            ('https://google.com/', 'chrome/browser/desktop/index.html'),  # Address with slash, path without slash
            ('https://github.com', '/Spacehug'),                           # Address without slash, path with slash
            ('https://vk.com/', '/id1')                                    # Address with slash, path with slash
        ]

        sample_data_should_equal = [
            'https://google.com/chrome/browser/desktop/index.html',
            'https://github.com/Spacehug',
            'https://vk.com/id1'
        ]

        for sample, result in zip(sample_data, sample_data_should_equal):
            address, path = sample
            self.assertEqual(absolutize_url(address, path), result)

    def test_reinforce_text(self):

        sample_data = [
            # Regular ASCII
            'The quick brown fox jumps over the lazy dog.',
            # Non-ASCII letters
            'Съешь ещё этих мягких французских булок, да выпей чаю.',
            # Shows the case for failing to parse Japanese into words (this will be wrapped alltogether)
            '火のない所に煙は立たぬ',
            # Changing text inside anchor
            '<a href=""><em>A phrase inside will get changed too!</em></a>',
            # The same words multiple times
            'The same words will get changed nicely too, see for yourself: words words words words.'
        ]

        sample_results = [
            # Spaces after the end are intentional (for styling concerns)
            'The <strong>quick</strong> <strong>brown</strong> fox <strong>jumps</strong> over the lazy dog. ',
            '<strong>Съешь</strong> ещё этих <strong>мягких</strong> <strong>французских</strong> <strong>булок</strong>, да <strong>выпей</strong> чаю. ',
            '<strong>火のない所に煙は立たぬ</strong> ',
            '<a href=""><em>A <strong>phrase</strong> <strong>inside</strong> will get <strong>changed</strong> too!</em></a> ',
            'The same <strong>words</strong> will get <strong>changed</strong> <strong>nicely</strong> too, see for <strong>yourself</strong>: <strong>words</strong> <strong>words</strong> <strong>words</strong> <strong>words</strong>. '
        ]

        for phrase, result in zip(sample_data, sample_results):
            self.assertEqual(reinforce_text(phrase), result)

    def test_url_parsing(self):

        sample_data = [
            'https://google.com/chrome/browser/desktop/index.html',
            'https://github.com/Spacehug',
            'http://127.0.0.1/admin/'
        ]

        sample_results = [
            'https://google.com/',
            'https://github.com/',
            'http://127.0.0.1/'
        ]

        for sample, result in zip(sample_data, sample_results):
            self.assertEqual(schemeful_domain(sample), result)

    def test_page_sterilization(self):

        sample_data = '''
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="description" content="">
    <meta name="author" content="">
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css" integrity="sha384-PsH8R72JQ3SOdhVi3uxftmaW6Vc51MKb0q5P2rRUpPvrszuE4W1povHYgTpBfshb" crossorigin="anonymous">
  </head>
  <body>
    <main role="main" class="container">
      <br>
      A page with small text, with a <a href="google.com">google.com link</a> and an emtpy link as image <a href=""></img></a>.
    </main>
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.3/umd/popper.min.js" integrity="sha384-vFJXuSJphROIrBnz7yo7oB41mKfc8JzQZiCq4NCceLEaO4IHwicKwpJf9c9IpFgh" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/js/bootstrap.min.js" integrity="sha384-alpBpkh1PFOepccYVYDB4do5UnbKysX5WZXm3XxPqe5iKTfUKjNkCk9SaVuEZflJ" crossorigin="anonymous"></script>
  </body>
</html>
'''

        sample_results = '<div> A page with small text, with a <a href="google.com">google.com link</a> and an emtpy link as image <a href=""></a>. </div>'

        self.assertEqual(sterilize_page(sample_data), sample_results)

    def test_normal_page_processing(self):

        sample_data = '<div>Sadly, but <a href="https://google.com/True">True</a> </div>'
        sample_results = '<div><strong>Sadly</strong>, but <a href="https://google.com/True"><em>True </em></a> </div>'

        self.assertEqual(process_page(sample_data, 'https://google.com/'), sample_results)

    def test_empty_link_removal(self):

        sample_data = '<div>A link: <a href=""></a> </div>'
        sample_results = '<div>A link: </div>'

        self.assertEqual(process_page(sample_data, 'https://google.com/'), sample_results)

    def test_fail_url_validation(self):

        sample_data = '<div>A link: <a href="/chrome/browser/desktop/index.html">Link </a> </div>'
        sample_results = '<div>A link: <a href="https://google.com/chrome/browser/desktop/index.html"><em>Link </em></a> </div>'

        self.assertEqual(process_page(sample_data, 'https://google.com/'), sample_results)

    def test_tail_parsing(self):

        sample_data = '<div><a href="#">Somewhere</a> over the rainbow</div>'
        sample_results = '<div><a href="https://google.com/#"><em><strong>Somewhere</strong> </em></a>over the <strong>rainbow</strong> </div>'

        self.assertEqual(process_page(sample_data, 'https://google.com/'), sample_results)


class MainViewTest(TestCase):

    def test_get_request(self):
        url = reverse('index')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

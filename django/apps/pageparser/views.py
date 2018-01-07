import requests

from django.shortcuts import render
from django.views import View
from requests.exceptions import ConnectionError

from .forms import URLSubmitForm
from .helpers import process_page, sterilize_page


class PageCleaner(View):

    form_class = URLSubmitForm
    template_name = 'pageparser/index.html'

    def get(self, request):
        form = self.form_class()

        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            target_url = form.cleaned_data['target_url']

            try:
                page_source = requests.get(target_url).text

            except ConnectionError:

                return render(
                    request,
                    self.template_name,
                    {
                        'form': form,
                        'page': '<div class="text-center">Не удалось соединиться с указанным сайтом :(</div>'
                    }
                )

            sterile_page = sterilize_page(page_source)
            ready_page = process_page(sterile_page, target_url)

            return render(request, self.template_name, {'form': form, 'page': ready_page})

        return render(request, self.template_name, {'form': form})

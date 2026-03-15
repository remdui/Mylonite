from django.http import JsonResponse
from django.views.generic import TemplateView, View

from .page_contexts import HomePageContextBuilder, WebPageContextFactory


class HealthView(View):
    def get(self, request):
        return JsonResponse({"status": "ok"})


class PageContextTemplateView(TemplateView):
    template_name = ""
    page_name = ""
    context_factory_class = WebPageContextFactory

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_factory = self.context_factory_class()
        context.update(context_factory.build_page_context(self.page_name))
        return context


class HomePageView(PageContextTemplateView):
    template_name = "web/home.html"
    page_name = HomePageContextBuilder.page_name


health = HealthView.as_view()
home = HomePageView.as_view()

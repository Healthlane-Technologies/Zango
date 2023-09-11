from django.views.generic import TemplateView
from ..plugins.frame.decorator import add_frame_context



class FrameTestView(TemplateView):

    template_name = 'example.html'

    @add_frame_context
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context.update(**self.get_frame_context(self.request))
        return context

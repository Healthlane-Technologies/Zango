from django.http import JsonResponse
from django.views.generic import TemplateView

from .helpers import x
from .helpers import y
from .helpers import z



def view1(request, *args, **kwargs):
    response = {"msg": "hello world"}    
    return JsonResponse(response)


# from condense-frame.frame.views.base import CondenseFrameBase
class View2(TemplateView):

    template_name = 'hello_world.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # frame_context = self.get_frame_context(**kwargs)
        print("request", self.request)
        # print(frame_context)
        # context['frame'] = self.get_frame_context(**kwargs)
        context.update(**kwargs)
        context.update(x=x)
        context.update(y=y)
        context.update(z=z)        
        return context


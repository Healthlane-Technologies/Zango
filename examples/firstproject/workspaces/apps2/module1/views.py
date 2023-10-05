from django.db.models import Q
from django.views.generic import TemplateView
from datetime import datetime
from zelthy.apps.dynamic_models.table.base import ModelTable
from zelthy.apps.dynamic_models.table.column import ModelCol, StringCol, NumericCol, SelectCol
from ..plugins.frame.decorator import add_frame_context
from ..plugins.crud.base import BaseCrudView
from .models import FHIRPatient
from .forms import FHIRPatientForm

class FrameTestView(TemplateView):

    template_name = 'example.html'

    @add_frame_context
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PatientTable(ModelTable):
                
        
    id = ModelCol(
                display_as='Patient ID',
                sortable=False,
                searchable=False
                )
    full_name = StringCol(
                sortable=True,
                searchable=True
                )
    age = StringCol(
                sortable=True,
                searchable=True,
                user_roles=["AnonymousUsers"]
                )
    user_role = ModelCol(
                sortable=False,
                searchable=False,
                roles=[
                   "Anonymous Uses" 
                ]
                )        
        
    row_actions = [{
                    "name": "Edit Patient",
                    "key": "edit",
                    "description": "Edit patient record",
                    "type": "form",
                    "form": FHIRPatientForm,
                    "roles": ["AnonymousUsers"]
                },
                {
                    "name": "Mark Active/Inactive",
                    "key": "mark_active_inactive",
                    "description": "Mark Patient Active/Inactive",
                    "type": "simple",
                    "confirmation_message": "Are you sure you want to perform this action?",
                    "roles": ["AnonymousUsers"]
                },
                {
                    "name": "Delete",
                    "key": "delete_patient",
                    "description": "Delete Patient",
                    "type": "simple",
                    "confirmation_message": "Are you sure you want to delete this action?",
                    "roles": ["AnonymousUsers"]
                }
                ]
    table_actions = [{
                    "name": "Delete",
                    "key": "delete",
                    "type": "simple",
                    "icon": ""
                }, {
                    "name": "Suspend",
                    "key": "suspend",
                    "type": "simple",
                    "icon": ""
                }]
            

    def id_getval(self, obj):
        return "<a href='#'>"+str(obj.id+10000)+"</a>"
        
    def full_name_getval(self, obj):
        return f"{obj.family} {obj.given}"
        
    def age_getval(self, obj):
        if not obj.birth_date:
                return "NA"
        else:                  
            today = datetime.today()
            age = today.year - obj.birth_date.year - 1 if today.month < obj.birth_date.month else today.year - obj.birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age

    def gender_getval(self, obj):
        if obj.gender == 'male':
            return "Male"
        elif obj.gender == 'female':
            return "Female"
        else:
            return "Others"
        
    def can_perform_row_action_mark_active_inactive(self, request, obj):
        return True
    
    def can_perform_row_action_edit(self, request, obj):
        return obj.active
    
    def process_row_action_mark_active_inactive(self, request, obj):
        obj.active = not obj.active
        obj.save()
        success = False
        response = {
            "message": "Marked as " + ("Active" if obj.active else "Inactive")
        }

        return success, response

    def process_row_action_delete_patient(self, request, obj):
        obj.delete()
        success = True
        response = {
            "message": "Successfully Deleted."
        }

        return success, response
    
        
    class Meta:
        model = FHIRPatient
        # fields = '__all__'
        fields = ['id', 'gender', 'city', 'state', 'country', 'user_role', 'identifier', 'active']
        # pagination = 10
        row_selector = {'enabled': True, 'multi': True}



class CrudTestView(BaseCrudView):

    page_title = "Patient Master"
    add_btn_title = "Add New"        
    table = PatientTable
    form = FHIRPatientForm

    

    def has_add_perm(self, request):
        return True
    


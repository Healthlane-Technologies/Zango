from django import forms

from .models import ProgramModel



class ProgramForm(forms.ModelForm):
    class Meta:
        model = ProgramModel
        fields = ['short_code', 'program_name', 'description', 'program_delivered_through', 'jsonfield_extra1']
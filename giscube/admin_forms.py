from django import forms

from .models import DBConnection


class DBConnectionForm(forms.ModelForm):
    class Meta:
        model = DBConnection
        widgets = {
            'password': forms.PasswordInput(render_value=True)
        }
        exclude = ()

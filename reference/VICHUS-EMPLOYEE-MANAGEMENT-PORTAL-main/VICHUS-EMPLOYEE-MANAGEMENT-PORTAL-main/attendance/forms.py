from django import forms
from django.contrib.auth.models import User
from .models import EmployeeProfile

class UserRegistrationForm(forms.ModelForm):
    ROLE_CHOICES = (
        ('developer', 'Developer Mode'),
        ('management', 'Management Mode'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, widget=forms.Select)
    employee_id = forms.CharField(max_length=20, required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")

        employee_id = cleaned_data.get("employee_id")
        if EmployeeProfile.objects.filter(employee_id=employee_id).exists():
            self.add_error('employee_id', 'An employee with this ID already exists.')

        return cleaned_data

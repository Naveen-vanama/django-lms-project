from django import forms
from .models import Course, Batch, Group
from users.models import CustomUser


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'code', 'description', 'instructor', 'status', 'credits', 'thumbnail')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'instructor': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instructor'].queryset = CustomUser.objects.filter(role='instructor')


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ('name', 'start_date', 'end_date', 'max_students')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'members')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'members': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, batch=None, **kwargs):
        super().__init__(*args, **kwargs)
        if batch:
            enrolled_students = CustomUser.objects.filter(
                enrollments__batch=batch
            )
            self.fields['members'].queryset = enrolled_students

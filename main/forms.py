from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import BlogPost


class BlogForm(forms.ModelForm):
    body = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = BlogPost
        fields = '__all__'

from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import BlogPost


class BlogForm(forms.ModelForm):
    title = forms.CharField(label='Tiêu đề', widget=forms.TextInput(attrs={'class': 'form-control'}))
    body = forms.CharField(label='Nội dung', widget=CKEditorUploadingWidget())
    type = forms.ChoiceField(label='Hiển thị cho', choices=BlogPost.TYPE_CHOICES,
                             widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = BlogPost
        fields = '__all__'


class EditBlogForm(forms.ModelForm):
    title = forms.CharField(label='Tiêu đề', widget=forms.TextInput(attrs={'class': 'form-control'}))
    body = forms.CharField(label='Nội dung', widget=CKEditorUploadingWidget())
    type = forms.ChoiceField(label='Hiển thị cho', choices=BlogPost.TYPE_CHOICES,
                             widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = BlogPost
        fields = '__all__'

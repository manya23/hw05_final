from django import forms
from . models import Post, Comment


class PostForm(forms.ModelForm):
    """Класс для формы создания нового поста."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """Класс для формы создания нового комментария."""
    class Meta:
        model = Comment
        fields = ('text', )

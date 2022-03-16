from django import forms
from django.contrib.auth.models import User
from .models import Profile, Post, Comment, Message, MessageContent
from datetime import date, datetime


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Email', 'required': 'true', 'autofocus': 'true'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Password', 'required': 'true'}))

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('User does not exist')
        user = User.objects.get(email=email)
        if not user.check_password(password):
            raise forms.ValidationError('Incorrect password')
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['email'].widget.attrs['required'] = 'true'
        self.fields['email'].widget.attrs['autofocus'] = 'true'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['placeholder'] = 'Password'
        self.fields['password'].widget.attrs['required'] = 'true'

    def get_user(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        user = User.objects.get(email=email)
        return user


class ProfileCoverChangeForm(forms.Form):
    cover = forms.ImageField(widget=forms.FileInput(
        attrs={'class': 'd-none', 'id': 'cover-select', 'hidden': 'true', 'onchange': 'form.submit()'}))

    def clean(self):
        cover = self.cleaned_data.get('cover')
        if not cover:
            raise forms.ValidationError('Cover is required')
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super(ProfileCoverChangeForm, self).__init__(*args, **kwargs)
        self.fields['cover'].widget.attrs['class'] = 'd-none'
        self.fields['cover'].widget.attrs['id'] = 'cover-select'
        self.fields['cover'].widget.attrs['hidden'] = 'true'
        self.fields['cover'].widget.attrs['onchange'] = 'form.submit()'


class ProfilePhotoChangeForm(forms.Form):
    photo = forms.ImageField(widget=forms.FileInput(
        attrs={'class': 'd-none', 'id': 'pp-select', 'hidden': 'true', 'onchange': 'form.submit()'}))

    def clean(self):
        photo = self.cleaned_data.get('photo')
        if not photo:
            raise forms.ValidationError('Photo is required')
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super(ProfilePhotoChangeForm, self).__init__(*args, **kwargs)
        self.fields['photo'].widget.attrs['class'] = 'd-none'
        self.fields['photo'].widget.attrs['id'] = 'pp-select'
        self.fields['photo'].widget.attrs['hidden'] = 'true'
        self.fields['photo'].widget.attrs['onchange'] = 'form.submit()'


class SearchForm(forms.Form):
    q = forms.CharField(label='Search', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Search', 'required': 'true', 'aria-label': 'Search'}))

    def clean(self):
        q = self.cleaned_data.get('q')
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['q'].widget.attrs['class'] = 'form-control'
        self.fields['q'].widget.attrs['placeholder'] = 'Search'
        self.fields['q'].widget.attrs['required'] = 'true'
        self.fields['q'].widget.attrs['aria-label'] = 'Search'


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'visibility', 'attachment']

    def clean(self):
        content = self.cleaned_data.get('content')
        if not content:
            raise forms.ValidationError('Content is required')
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['class'] = 'form-control'
        self.fields['content'].widget.attrs['placeholder'] = 'What\'s on your mind?'
        self.fields['content'].widget.attrs['required'] = 'true'
        self.fields['content'].widget.attrs['rows'] = '2'
        self.fields['content'].widget.attrs['maxlength'] = '500'
        self.fields['visibility'].widget.attrs['class'] = 'form-select form-select-sm fa-pull-right'
        self.fields['visibility'].widget.attrs['aria-label'] = '.form-select-sm'
        self.fields['visibility'].widget.attrs['style'] = 'width: auto !important;'
        self.fields['attachment'].widget.attrs['class'] = 'form-control-file'
        self.fields['attachment'].widget.attrs['id'] = 'attachment-select'
        self.fields['attachment'].widget.attrs['hidden'] = 'true'


class DateSelectorWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        days = [(day, day) for day in range(1, 32)]
        months = [(month, month) for month in range(1, 13)]
        years = [(year, year) for year in range(datetime.now().year + 1, datetime.now().year - 100, -1)]
        widgets = [
            forms.Select(attrs=attrs, choices=days),
            forms.Select(attrs=attrs, choices=months),
            forms.Select(attrs=attrs, choices=years),
        ]
        super().__init__(widgets, attrs)

    def subwidgets(self, name, value, attrs=None):
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        # value is a list of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)
        output = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id')
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, i))
            output.append(widget.render(name + '_%s' % i, widget_value, final_attrs))
        return output

    def decompress(self, value):
        if isinstance(value, date):
            return [value.day, value.month, value.year]
        elif isinstance(value, str):
            year, month, day = value.split('-')
            return [day, month, year]
        return [None, None, None]

    def value_from_datadict(self, data, files, name):
        day, month, year = super().value_from_datadict(data, files, name)
        # DateField expects a single string that it can parse into a date.
        return '{}-{}-{}'.format(year, month, day)


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Password', 'required': 'true', 'aria-label': 'Password'}))
    # use custom DateSelectorWidget to handle date selection
    birth_date = forms.DateField(widget=DateSelectorWidget(attrs={'class': 'form-control'}), required=True)
    GENDERS = [('Male', 'Male'), ('Female', 'Female')]
    gender = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class': 'col-5 form-check form-check-inline ms-3'}),
                               choices=GENDERS)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

    def clean(self):
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        birth_date = self.cleaned_data.get('birth_date')
        gender = self.cleaned_data.get('gender')
        if not first_name:
            raise forms.ValidationError('First name is required')
        if not last_name:
            raise forms.ValidationError('Last name is required')
        if not username:
            raise forms.ValidationError('Username is required')
        if not email:
            raise forms.ValidationError('Email is required')
        if not password:
            raise forms.ValidationError('Password is required')
        if not birth_date:
            raise forms.ValidationError('Birth date is required')
        if not gender:
            raise forms.ValidationError('Gender is required.')
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['class'] = 'form-control'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['first_name'].widget.attrs['required'] = 'true'
        self.fields['first_name'].widget.attrs['aria-label'] = 'First name'
        self.fields['last_name'].widget.attrs['class'] = 'form-control'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last name'
        self.fields['last_name'].widget.attrs['required'] = 'true'
        self.fields['last_name'].widget.attrs['aria-label'] = 'Last name'
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['username'].widget.attrs['required'] = 'true'
        self.fields['username'].widget.attrs['aria-label'] = 'Username'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['email'].widget.attrs['required'] = 'true'
        self.fields['email'].widget.attrs['aria-label'] = 'Email'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['placeholder'] = 'Password'
        self.fields['password'].widget.attrs['required'] = 'true'
        self.fields['password'].widget.attrs['aria-label'] = 'Password'
        self.fields['password'].widget.attrs['type'] = 'password'
        self.fields['birth_date'].widget.attrs['class'] = 'm-auto form-control w-25'
        self.fields['birth_date'].widget.attrs['placeholder'] = 'Birthdate'
        self.fields['birth_date'].widget.attrs['required'] = 'true'
        self.fields['birth_date'].widget.attrs['aria-label'] = 'Birthdate'
        # self.fields['birth_date'].widget.attrs['style'] = 'width: 10px'
        self.fields['gender'].widget.attrs['class'] = ''
        self.fields['gender'].widget.attrs['placeholder'] = 'Gender'
        self.fields['gender'].widget.attrs['required'] = 'true'
        self.fields['gender'].widget.attrs['aria-label'] = 'Gender'


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

    def clean(self):
        content = self.cleaned_data.get('content')
        if not content:
            raise forms.ValidationError('Content is required')
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['class'] = 'form-control'
        self.fields['content'].widget.attrs['placeholder'] = 'Write your comment here...'
        self.fields['content'].widget.attrs['required'] = 'true'
        self.fields['content'].widget.attrs['rows'] = '3'
        self.fields['content'].widget.attrs['maxlength'] = '500'


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

    def clean(self):
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        if not first_name:
            raise forms.ValidationError('First name is required')
        if not last_name:
            raise forms.ValidationError('Last name is required')
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['class'] = 'form-control text-center'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['first_name'].widget.attrs['required'] = 'true'
        self.fields['first_name'].widget.attrs['type'] = 'text'
        self.fields['last_name'].widget.attrs['class'] = 'form-control text-center'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last name'
        self.fields['last_name'].widget.attrs['required'] = 'true'
        self.fields['last_name'].widget.attrs['type'] = 'text'


class ProfileEditForm(forms.ModelForm):
    GENDERS = [('Male', 'Male'), ('Female', 'Female')]
    gender = forms.ChoiceField(widget=forms.Select(attrs={'class': 'col-5 form-check form-check-inline ms-3'}),
                               choices=GENDERS)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    duration_start = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    duration_end = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    class Meta:
        model = Profile
        exclude = ['profile_pic', 'cover_pic', 'friends', 'user']

    def clean(self):
        gender = self.cleaned_data.get('gender')
        birth_date = self.cleaned_data.get('birth_date')
        family = self.cleaned_data.get('family')
        current_city = self.cleaned_data.get('current_city')
        hometown = self.cleaned_data.get('hometown')
        phone_number = self.cleaned_data.get('phone_number')
        website = self.cleaned_data.get('website')
        address = self.cleaned_data.get('address')
        country = self.cleaned_data.get('country')
        bio = self.cleaned_data.get('bio')
        university = self.cleaned_data.get('university')
        major = self.cleaned_data.get('major')
        gpa = self.cleaned_data.get('gpa')
        company = self.cleaned_data.get('company')
        position = self.cleaned_data.get('position')
        duration_start = self.cleaned_data.get('duration_start')
        duration_end = self.cleaned_data.get('duration_end')
        duration_current = self.cleaned_data.get('duration_current')
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        self.fields['gender'].widget.attrs['class'] = 'form-select w-50'
        self.fields['gender'].widget.attrs['placeholder'] = 'Gender'
        self.fields['birth_date'].widget.attrs['class'] = 'form-control w-50'
        self.fields['birth_date'].widget.attrs['placeholder'] = 'Date of birth'
        self.fields['birth_date'].widget.attrs['type'] = 'date'
        self.fields['family'].widget.attrs['class'] = 'form-control w-50'
        self.fields['family'].widget.attrs['placeholder'] = 'Family Members'
        self.fields['current_city'].widget.attrs['class'] = 'form-control w-50'
        self.fields['current_city'].widget.attrs['placeholder'] = 'Current city'
        self.fields['hometown'].widget.attrs['class'] = 'form-control w-50'
        self.fields['hometown'].widget.attrs['placeholder'] = 'Hometown'
        self.fields['phone_number'].widget.attrs['class'] = 'form-control'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Phone number'
        self.fields['phone_number'].widget.attrs['id'] = 'phone'
        self.fields['phone_number'].widget.attrs['name'] = 'phone'
        self.fields['phone_number'].widget.attrs['type'] = 'tel'
        self.fields['website'].widget.attrs['class'] = 'form-control w-50'
        self.fields['website'].widget.attrs['placeholder'] = 'Website'
        self.fields['address'].widget.attrs['class'] = 'form-control w-50'
        self.fields['address'].widget.attrs['placeholder'] = 'Address'
        self.fields['country'].widget.attrs['class'] = 'form-control w-50'
        self.fields['country'].widget.attrs['placeholder'] = 'Country'
        self.fields['country'].widget.attrs['id'] = 'country_selector'
        self.fields['bio'].widget.attrs['class'] = 'form-control'
        self.fields['bio'].widget.attrs['placeholder'] = 'Bio'
        self.fields['bio'].widget.attrs['id'] = 'bio-textarea'
        self.fields['bio'].widget.attrs['rows'] = '5'
        self.fields['university'].widget.attrs['class'] = 'form-control w-50'
        self.fields['university'].widget.attrs['placeholder'] = 'University'
        self.fields['major'].widget.attrs['class'] = 'form-control w-50'
        self.fields['major'].widget.attrs['placeholder'] = 'Major'
        self.fields['gpa'].widget.attrs['class'] = 'form-control w-50'
        self.fields['gpa'].widget.attrs['placeholder'] = 'GPA'
        self.fields['gpa'].widget.attrs['type'] = 'number'
        self.fields['gpa'].widget.attrs['max'] = '4.0'
        self.fields['gpa'].widget.attrs['step'] = '0.01'
        self.fields['company'].widget.attrs['class'] = 'form-control w-50'
        self.fields['company'].widget.attrs['placeholder'] = 'Company'
        self.fields['position'].widget.attrs['class'] = 'form-control w-50'
        self.fields['position'].widget.attrs['placeholder'] = 'Position'
        self.fields['duration_start'].widget.attrs['class'] = 'form-control'
        self.fields['duration_start'].widget.attrs['placeholder'] = 'Duration start'
        self.fields['duration_start'].widget.attrs['id'] = 'start-date'
        self.fields['duration_start'].widget.attrs['type'] = 'date'
        self.fields['duration_end'].widget.attrs['class'] = 'form-control'
        self.fields['duration_end'].widget.attrs['placeholder'] = 'Duration end'
        self.fields['duration_end'].widget.attrs['id'] = 'end-date'
        self.fields['duration_end'].widget.attrs['type'] = 'date'
        self.fields['duration_current'].widget.attrs['placeholder'] = 'Duration current'
        self.fields['duration_current'].widget.attrs['id'] = 'present-work'
        self.fields['duration_current'].widget.attrs['onclick'] = 'hideEndInput(this)'
        self.fields['duration_current'].widget.attrs['type'] = 'checkbox'


class NewMessageForm(forms.ModelForm):
    class Meta:
        model = MessageContent
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Type your message here...', 'rows': '3'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        if len(content) < 1:
            raise forms.ValidationError('Message is empty')
        return cleaned_data

    def save(self, commit=True):
        message = super().save(commit=False)
        message.sender = self.initial['sender']
        message.receiver = self.initial['receiver']
        message.save()
        return message

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['class'] = 'form-control'
        self.fields['content'].widget.attrs['placeholder'] = 'Type your message here...'
        self.fields['content'].widget.attrs['rows'] = '3'
        self.fields['content'].widget.attrs['id'] = 'message-textarea'

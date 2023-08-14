from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Post, Comment
from .forms import CommentForm
from users.models import UserProfile
import time
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from APIs.generative_AI_api import chatGPT_api
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)

@login_required
def forum(request):
    context = {
        'posts': Post.objects.all()
    }
    return render(request, 'feed/forum.html', context)

@method_decorator(login_required, name='dispatch')
class PostListView(ListView):
    model = Post
    template_name = 'feed/forum.html'  # view look for this pattern HTML template: <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 2

    def get_queryset(self):
        user = User.objects.filter(username=self.request.user).first()

        if user.is_superuser:
            return Post.objects.all().order_by('-date_posted')
     
        #userProfile= UserProfile.objects.filter(user_id=user.id).first()
        #print('ALL user profile id ', UserProfile.objects.values('user_id'))


        if user.user_profile.role=='mentee':
            mentor_email = user.user_profile.mentor_email
            userProfiles= UserProfile.objects.filter(mentor_email=mentor_email)
            mentee_users = User.objects.filter(id__in=userProfiles.values('user_id'))
            
            return Post.objects.filter(author__in=mentee_users.values('id')).order_by('-date_posted')
        
        elif user.user_profile.role=='mentor':
            mentor_email = user.email
            userProfiles= UserProfile.objects.filter(mentor_email=mentor_email)
            mentee_users = User.objects.filter(id__in=userProfiles.values('user_id'))
            
            return Post.objects.filter(author__in=mentee_users.values('id')).order_by('-date_posted')
            
        return user.post_set.all().order_by('-date_posted')
    

class UserPostListView(ListView):
    model = Post
    template_name = 'feed/user_posts.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    paginate_by = 2

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')
    

@method_decorator(login_required, name='dispatch')
class PostDetailView(DetailView):
    model = Post

    def get_context_data(self , **kwargs):
        data = super().get_context_data(**kwargs)
        connected_comments = Comment.objects.filter(comment_post=self.get_object())
        number_of_comments = connected_comments.count()
        print('number_of_comments :: ', number_of_comments)
        data['comments'] = connected_comments
        data['no_of_comments'] = number_of_comments
        data['comment_form'] = CommentForm()
        return data
    
    def post(self , request , *args , **kwargs):
        if self.request.method == 'POST':
            comment_form = CommentForm(self.request.POST)
            
            if comment_form.is_valid():
                content = comment_form.cleaned_data['content']
    
            new_comment = Comment(content=content , author = self.request.user , comment_post=self.get_object() )
            new_comment.save()
            return redirect(self.request.path_info)

@login_required
def postDetailView(request, pk):
    print('post request param :: ', pk)
    post = get_object_or_404(Post, pk=pk)
    print('POST:: ', post)
    context = {
        'post': post
    }
    return render(request, 'feed/post_detail.html', context)

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False

@login_required
def survey_question(request):
    return render(request, 'feed/survey.html', {'title': 'Survey'})

@login_required
def mentee_stat(request):
    return render(request, 'feed/stat.html', {'title': 'Stat'})

def generate_respose_with_AI(request):
    post_value = request.GET.get('post_value')
    time.sleep(5)
    generated_response = chatGPT_api(post_value)
    return JsonResponse({'generated_response': generated_response})

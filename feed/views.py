from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Post, Comment
from .forms import CommentForm, PostForm
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
from django.views.decorators.csrf import csrf_exempt
import logging
logger = logging.getLogger(__name__)

#@csrf_exempt
@login_required
def forum(request):
    context = {
        'posts': Post.objects.all()
    }
    return render(request, 'feed/forum.html', context)

#@csrf_exempt
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

'''   
#@csrf_exempt
class UserPostListView(ListView):
    model = Post
    template_name = 'feed/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 2

    def get_queryset(self):
        self.profile_user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=self.profile_user).order_by('-date_posted')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user == self.profile_user:
            # Count all posts for the author
            context['post_count'] = self.get_queryset().count()
        else:
            # Count only non-anonymous posts for others
            context['post_count'] = self.get_queryset().filter(anonymous=False).count()
        return context
'''    

class UserPostListView(ListView):
    model = Post
    template_name = 'feed/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 2

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        if self.request.user == user:
            # Show all posts for the author
            return Post.objects.filter(author=user).order_by('-date_posted')
        else:
            # Show only non-anonymous posts for other users
            return Post.objects.filter(author=user, anonymous=False).order_by('-date_posted')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        context['profile_user'] = user

        if self.request.user == user:
            # Count all posts for the author
            context['total_post_count'] = Post.objects.filter(author=user).count()
        else:
            # Count only non-anonymous posts for other users
            context['total_post_count'] = Post.objects.filter(author=user, anonymous=False).count()

        return context

    

#@csrf_exempt
@method_decorator(login_required, name='dispatch')
class PostDetailView(DetailView):
    model = Post

    def get_context_data(self , **kwargs):
        data = super().get_context_data(**kwargs)
        connected_comments = Comment.objects.filter(comment_post=self.get_object())
        number_of_comments = connected_comments.count()
        logger.debug('Number of comments ::  {number_of_comments}')
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

#@csrf_exempt
@login_required
def postDetailView(request, pk):
    logger.debug('Post request param ::  {pk}')
    post = get_object_or_404(Post, pk=pk)
    context = {
        'post': post
    }
    return render(request, 'feed/post_detail.html', context)

#@csrf_exempt
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
#@csrf_exempt
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

#@csrf_exempt
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

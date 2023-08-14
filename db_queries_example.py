# django models/objects are accessible from shell
# To run shell: python manage.py shell


from feed.models import Post, Comment
from django.contrib.auth.models import User

# get all users/post
User.objects.all()
Post.objects.all()

# create a post
user = User.objects.all().first()
post_13 = Post(title='post13', content='create post using model objects', author=user)
post_13.save()

post_14 = Post(title='post 14', content='testing python shell', author_id=user.id)
post_14.save()

# get first user
User.objects.first()

# filter user
User.objects.filter(username='mentee11')
User.objects.filter(username='mentee11').first() # if multiple user

# capture in a variable
user = User.objects.first()
user = User.objects.filter(username='mentee11')
user = User.objects.filter(username='mentee11').first()

# capture attribute, not working after filtering have to use first()
user.id
user.pk

user= User.objects.get(id=1)
user= User.objects.get(email='mentee11@mail.com')

post = Post.objects.first()
author_email = post.author.email

# get post written by a specific user
# modelname_set
user.post_set
user.post_set.all()

# create a post using the modelname_set, no need to set author and save
user.post_set.create(title='post 15', content='create post using modelname_set')


# check all attribute name
user.__dict__.keys()
#dict_keys(['_state', 'id', 'password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined'])
#dict_keys(['_state', 'id', 'user_id', 'role', 'mentor_email'])

# get posts's all comment and user
post = Post.objects.first()
comments = post.comment_set.all()

for comment in comments:
    content_text = comment.content
    author_name = comment.author.username  

    print(content_text)
    print(author_name)
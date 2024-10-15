import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import Post, Comment

# Export Post model data to CSV
def export_posts_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="posts.csv"'

    writer = csv.writer(response)
    # Write the header for Post fields
    writer.writerow(['ID', 'Title', 'Content', 'Date Posted', 'Author', 'Anonymous', 'Organization'])

    # Write the data rows
    for post in queryset:
        writer.writerow([post.id, post.title, post.content, post.date_posted, post.author.username, post.anonymous, post.organization.name])

    return response

export_posts_to_csv.short_description = 'Export selected Posts to CSV'

# Export Comment model data to CSV
def export_comments_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="comments.csv"'

    writer = csv.writer(response)
    # Write the header for Comment fields
    writer.writerow(['ID', 'Content', 'Date Posted', 'Post ID', 'Post Title', 'Author'])

    # Write the data rows
    for comment in queryset:
        writer.writerow([comment.id, comment.content, comment.date_posted, comment.comment_post.id, comment.comment_post.title, comment.author.username])

    return response

export_comments_to_csv.short_description = 'Export selected Comments to CSV'

# Register the actions in the Admin interface
class PostAdmin(admin.ModelAdmin):
    actions = [export_posts_to_csv]

class CommentAdmin(admin.ModelAdmin):
    actions = [export_comments_to_csv]

admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
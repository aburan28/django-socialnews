from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from helpers import *
import bforms
import exceptions



def main(request):
    "Sitewide main page"
    if request.user.is_authenticated():
        subs = SubscribedUser.objects.filter(user = request.user)
        topics = [sub.topic for sub in subs]
        links = Link.objects.get_query_set_with_user(request.user).filter(topic__in = topics).select_related()
    else:
        links = Link.objects.all().select_related()
    links, page_data = get_paged_objects(links, request, defaults.LINKS_PER_PAGE)
    tags = Tag.objects.filter(topic__isnull = True).select_related().order_by()
    if request.user.is_authenticated():
        subscriptions = SubscribedUser.objects.filter(user = request.user).select_related(depth = 1)
    else:
        subscriptions = SubscribedUser.objects.get_empty_query_set()
    top_topics = Topic.objects.all().order_by('-num_links')[:defaults.TOP_TOPICS_ON_MAINPAGE]
    new_topics = Topic.objects.all().order_by('-updated_on')[:defaults.NEW_TOPICS_ON_MAINPAGE]
    payload = {'links':links, 'tags':tags, 'subscriptions':subscriptions, 'top_topics':top_topics, 'new_topics':new_topics}
    return render(request, payload, 'news/main.html')
    
    
def topic_main(request, topic_name, order_by = None):
    try:
        topic = get_topic(request, topic_name)
    except exceptions.NoSuchTopic, e:
        url = '/createtopic/'#reverse('createtopic');
        return HttpResponseRedirect('%s?topic_name=%s' % (url, topic_name))
    tags = Tag.objects.filter(topic = topic).select_related()
    if request.user.is_authenticated():
        links = Link.objects.get_query_set_with_user(request.user).filter(topic = topic).select_related()
    else:
        links = Link.objects.filter(topic = topic).select_related()
    if order_by == 'new':
        links = links.order_by('-created_on')
    links, page_data = get_paged_objects(links, request, defaults.LINKS_PER_PAGE)
    subscribed = False
    if request.user.is_authenticated():
        subscriptions = SubscribedUser.objects.filter(user = request.user).select_related(depth = 1)
        try:
            SubscribedUser.objects.get(topic = topic, user = request.user)
            subscribed = True
        except SubscribedUser.DoesNotExist:
            pass
    else:
        subscriptions = SubscribedUser.objects.get_empty_query_set()
    
    payload = dict(topic = topic, links = links, subscriptions=subscriptions, tags=tags, subscribed=subscribed)
    return render(request, payload, 'news/topic_main.html')



@login_required    
def create(request, topic_name=None):
    if request.method == 'GET':
        if not topic_name:
            topic_name = request.GET.get('topic_name', '')
            form = bforms.NewTopic(user = request.user, topic_name = topic_name)
        else:
            form = bforms.NewTopic(user = request.user, topic_name = topic_name)
    elif request.method == 'POST':
        form = bforms.NewTopic(user = request.user, data = request.POST)
        if form.is_valid():
            topic = form.save()
            return HttpResponseRedirect(topic.get_absolute_url())
            
    payload = {'form':form}
    return render(request, payload, 'news/create_topic.html')

@login_required
def topic_manage(request, topic_name):
    """Allow moderators to manage a topic.
    Only moderators of the topic have access to this page.
    """
    topic = get_topic(request, topic_name)
    "if logged in user, not a moderator bail out."
    try:
        subs = SubscribedUser.objects.get(topic = topic, user = request.user)
        if not subs.is_moderator():
            return HttpResponseForbidden("%s is not a moderator for %s. You can't access this page." % (request.user.username, topic.full_name))
    except SubscribedUser.DoesNotExist:
        return HttpResponseForbidden("%s is not a moderator for %s. You can't access this page." % (request.user.username, topic.full_name))
    subs = SubscribedUser.objects.select_related().filter(topic = topic)
    if request.method=='POST':
        username = request.POST['username']
        user = User.objects.get(username = username)
        if request.POST.has_key('promote'):
            sub = SubscribedUser.objects.get(user = user, topic = topic)
            sub.set_group('Moderator')
        if request.POST.has_key('demote'):
            sub = SubscribedUser.objects.get(user = user, topic = topic)
            sub.set_group('Member')        
    payload = {'topic':topic, 'subs':subs }
    return render(request, payload, 'news/manage_topic.html')

def topic_about(request, topic_name):
    topic = get_topic(request, topic_name)
    payload = {'topic':topic}
    return render(request, payload, 'news/topic_about.html')

    
    

    
    
    
    
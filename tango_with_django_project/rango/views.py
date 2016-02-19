from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from rango.forms import CategoryForm, PageForm, ChangePassword
from rango.models import Category, Page, User, UserProfile
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
from rango.bing_search import run_query
from django.shortcuts import redirect

from registration import signals
from registration.users import UserModel
from registration.backends.simple.views import RegistrationView

# --- USER RELATED VIEWS ----
#Trying to Hack a change password form for the user

class MyRegistrationView(RegistrationView):
    def register(self, request, **cleaned_data):
        # Create a new User
        username, email, password = cleaned_data['username'], cleaned_data['email'], cleaned_data['password1']
        new_user_object = UserModel().objects.create_user(username, email, password)

        # And links that user to a new (empty) UserProfile
        profile = UserProfile(user=new_user_object)
        profile.save()

        new_user = authenticate(username=username, password=password)
        login(request, new_user)
        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        return new_user

    def get_success_url(self, request, user):
        return('/rango/', (), {})


@login_required()
def edit_profile(request):
    # a HTTP POST?
    if request.method == "POST":
        form = ChangePassword(request.POST)

        # have we been provided with a valid form
        if form.is_valid():
            # save the new category
            form.save(commit=True)

            # now call the index() view
            # the user will be shown the homepage
            return index(request)
        else:
            # supplied form had errors
            print form.errors
    else:
        # if the request was not a post , display the form to enter details
        form = ChangePassword()
        #form.fields["Email"].initial = request.email
    # bad form ( or form details , no form supplied...
    # Render the form with error messages if any
    response = render(request, 'rango/edit_profile.html', {"form": form})
    return response


def index(request):
    context_dict = {}
    # Query the database for a list of ALL categories currently stored.
    # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary which will be passed to the template engine.
    category_list = Category.objects.order_by('-likes')[:5]
    view_list = Page.objects.order_by('-views')[:5]
    context_dict['categories'] = category_list
    context_dict['view_list'] = view_list


    # Get the number of visits to the site.
    # We use the COOKIES.get() function to obtain the visits cookie.
    # If the cookie exists, the value returned is casted to an integer.
    # If the cookie doesn't exist, we default to zero and cast that.
    visits = request.session.get('visits')
    if not visits:
        visits = 1
    reset_last_visit_time = False

    last_visit = request.session.get('last_visit')
    if last_visit:
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        if (datetime.now() - last_visit_time).seconds > 0:
            # ...reassign the value of the cookie to +1 of what it was before...
            visits = visits + 1
            # ...and update the last visit cookie, too.
            reset_last_visit_time = True
    else:
        # Cookie last_visit doesn't exist, so create it to the current date/time.
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits
    context_dict['visits'] = visits

    response = render(request,'rango/index.html', context_dict)

    return response


def about(request):
    # If the visits session varible exists, take it and use it.
    # If it doesn't, we haven't visited the site so set the count to zero.
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0

    # remember to include the visit data
    return render(request, 'rango/about.html', {'visits': count})


def category(request, category_name_slug):
       # Create a context dictionary which we can pass to the template rendering engine
    context_dict = {}
    try:
        # Can we find a category name slug with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name

        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        pages = Page.objects.filter(category=category)

        context_dict['pages'] = pages
        context_dict['category'] = category
        context_dict['category_name_slug'] =category.slug
    except Category.DoesNotExist:
        pass

    return render(request, 'rango/category.html', context_dict)

@login_required
def add_category(request):
    # a HTTP POST?
    if request.method == "POST":
        form = CategoryForm(request.POST)

        # have we been provided with a valid form
        if form.is_valid():
            # save the new category
            form.save(commit=True)

            # now call the index() view
            # the user will be shown the homepage
            return index(request)
        else:
            # supplied form had errors
            print form.errors
    else:
        # if the request was not a post , display the form to enter details
        form = CategoryForm()

    # bad form ( or form details , no form supplied...
    # Render the form with error messages if any
    return render(request, "rango/add_category.html", {"form": form})

@login_required
def add_page(request, category_name_slug):
    try:
        cat = Category.objects.get(slug=category_name_slug)
        print "test"
        print cat
    except Category.DoesNotExist:
            cat = None
            print "test2"

    if request.method == "POST":
        print "Method was POST"
        form = PageForm(request.POST)
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()
                # probably better to use a redicrect here
                return category(request, category_name_slug)
        else:
            print form.errors
    else:
        print "Method was not POST"
        print cat, category_name_slug
        form = PageForm()

    context_dict = {"form": form, "category": cat, 'category_name_slug': category_name_slug}

    return render(request, "rango/add_page.html", context_dict)



@login_required
def restricted(request):
    return render(request, "rango/restricted.html", {})


def search(request):

    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    return render(request, 'rango/search.html', {'result_list': result_list})

def track_url(request):
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)
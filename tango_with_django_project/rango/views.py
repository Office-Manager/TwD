from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


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
    return render(request, 'rango/index.html', context_dict)

def about(request):
    return render(request, 'rango/about.html')


def category(request, category_name_slug):
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


def register(request):

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # if its not a HTTP POST we're interested in processing form data
    if request.method == "POST":
        # Attempt to grab imformation from the raw form information
        # Note that we make use of both UserForm and UserProfileForm
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method
            # Once hashed, we can update the user object
            user.set_password(user.password)
            user.save()

            #now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselvesm we set commit=False
            # This delays saving the model until we're ready to avoid integrity problems
            profile = profile_form.save(commit=False)
            profile.user = user

            # did the user provide a profile picture ?
            # if so we need to get it from the input form and put it in the userProfile  model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # now we save the UserProfile model instance
            profile.save()

            #Update our variable variable to tell the template registration was successful
            registered = True
        # Invalid form or forms
        # print problems to terminal/
        # THey'll alos need to be shown to user
        else:
            print user_form.errors, profile_form.errors

    #Not a http post , so we render our form using two modelform instances
    # These forms will be blank , ready for user input

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # render the template depending on the context
    return render(request,
                  'rango/register.html',
                  {'user_form': user_form, 'profile_form': profile_form, 'registered': registered})


def user_login(request):

    # if the request is HTTP POST try to pull out the relevant information.
    if request.method == "POST":
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
                # We use request.POST.get('<variable>') as opposed to request.POST['<variable>'],
                # because the request.POST.get('<variable>') returns None, if the value does not exist,
                # while the request.POST['<variable>'] will raise key error exception
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username = username , password = password)

        # if we have a user object, the details are correct.
        # if None , no user with matching credentials was found.
        if user:
            # is the account active ? it could have been disabled.
            if user.is_active:
                # if the account is valid and active , we can log the user in.
                # we'll send the user back to the homepage
                login(request,user)
                return HttpResponseRedirect("/rango/")
            else:
                # an inactive account was used - no logging in!
                return HttpResponse("youur Rango account is disabled.")
        else:
            # bad login details entered , we can't log the user in
            print "invalid login details : {0} , {1}".format(username, password)
            return HttpResponse("Invalid login details supplied")

    # The request is not a HTTP post , so display the login form
    # this scenario would most like be the http GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank disctionary object...
        return render(request, "rango/login.html", {})

@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")

# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')
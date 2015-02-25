from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from rango.models import Category, Page
from rango.forms import CategoryForm , PageForm

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
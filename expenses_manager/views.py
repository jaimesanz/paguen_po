# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login
from forms import UserForm, UsuarioForm
from django.contrib.auth.decorators import login_required


def index(request):
	a = 5
	b = 10
	# locals() creates a dict() object with all the variables from the local scope. We are passing it to the template
	return render(request, 'index.html', locals())

@login_required
def login_test(request):
    return render(request, "login_test.html", locals())


def register(request):
    # this method was created using the following tutorial: http://www.tangowithdjango.com/book/chapters/login.html

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UsuarioForm.
        user_form = UserForm(data=request.POST)
        usuario_form = UsuarioForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and usuario_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the Usuario instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            usuario = usuario_form.save(commit=False)
            usuario.user_id = user

            # Now we save the Usuario model instance.
            usuario.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, usuario_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        usuario_form = UsuarioForm()

    # Render the template depending on the context.
    return render(request, 'register.html',{'user_form': user_form, 'usuario_form': usuario_form, 'registered': registered})


def user_login(request):
    # this method was created using the following tutorial: http://www.tangowithdjango.com/book/chapters/login.html

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/login_test')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request ,'login.html', {})



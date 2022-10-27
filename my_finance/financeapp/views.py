from datetime import datetime, date, timedelta

from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required

from .models import Account, Balance, Category, User
from .forms import CategoryForm, BalanceForm

user_balance = 0.0
main_err = ''
date_start = None
date_end = None


# Create your views here.
def main(request):
    global user_balance, main_err, date_start, date_end
    operations = []
    dr_sum, cr_sum = 0.00, 0.00
    period_button = 'All Time'
    if main_err:
        err, main_err = main_err, ''
    else:
        err = ''
    if request.user.is_authenticated:
        balance = Account.objects.filter(user_id=request.user).first()
        user_balance = balance.sum
        if date_start is None:
            period_button = 'All Time'
            operations = Balance.objects.filter(user_id=request.user).all()
            dr_op = Balance.objects.filter(user_id=request.user, category__dr_cr=0).all()
            cr_op = Balance.objects.filter(user_id=request.user, category__dr_cr=1).all()
        else:
            next_day = date_end + timedelta(days=1)
            period_button = f'{date_start.strftime("%d %b %Y")} - {date_end.strftime("%d %b %Y")}'
            operations = Balance.objects.filter(user_id=request.user, performed__gte=date_start,
                                                performed__lte=next_day).all()
            dr_op = Balance.objects.filter(user_id=request.user, category__dr_cr=0, performed__gte=date_start,
                                           performed__lte=next_day).all()
            cr_op = Balance.objects.filter(user_id=request.user, category__dr_cr=1, performed__gte=date_start,
                                           performed__lte=next_day).all()
        dr_sum = sum([op.sum for op in dr_op])
        cr_sum = sum([op.sum for op in cr_op])
    return render(request, 'financeapp/index.html',
                  {'user_balance': user_balance, 'operations': operations, 'deb_sum': dr_sum, 'cr_sum': cr_sum,
                   'error': err, 'period': period_button})


@login_required
def user_logout(request):
    logout(request)
    return redirect('main')


def user_login(request):
    if request.method == 'GET':
        return render(request, 'financeapp/login.html', {'form': AuthenticationForm()})
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'financeapp/login.html',
                          {'form': AuthenticationForm(), 'error': 'Username or password didn\'t match'})
        login(request, user)
        balance = Account.objects.filter(user_id=request.user).first()
        if not balance:
            balance = Account.objects.create(user_id=request.user, sum=0.00)
            balance.save()
        return redirect('main')


def user_signup(request):
    if request.method == 'GET':
        return render(request, 'financeapp/signup.html', {'form': UserCreationForm()})
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(request.POST['username'], password=request.POST['password1'])
                user.save()
                return redirect('user_login')
            except IntegrityError as err:
                return render(request, 'financeapp/signup.html',
                              {'form': UserCreationForm(), 'error': 'Username already exist!'})
        else:
            return render(request, 'financeapp/signup.html',
                          {'form': UserCreationForm(), 'error': 'Password did not match'})


@login_required
def view_catigories(request):
    global user_balance, main_err
    if main_err:
        err, main_err = main_err, ''
    else:
        err = ''
    category_list = Category.objects.filter(user_id=request.user).order_by('dr_cr', 'name').all()
    return render(request, 'financeapp/categories.html',
                  {'classes': category_list, 'user_balance': user_balance, 'error': err})


@login_required
def new_category(request):
    if request.method == 'POST':
        try:
            dr_cr_switch = request.POST.get('switch-category')
            form = CategoryForm(request.POST)
            new_category = form.save(commit=False)
            new_category.user_id = request.user
            if dr_cr_switch is None:
                new_category.dr_cr = False
            else:
                new_category.dr_cr = True
            new_category.save()
            return redirect(to='view_categories')
        except IntegrityError as err:
            return render(request, 'financeapp/category.html',
                          {'form': CategoryForm(), 'error': 'Category will be unique!'})
    return render(request, 'financeapp/category.html', {'form': CategoryForm()})


@login_required
def delete_category(request, ctg_id):
    global user_balance, main_err
    del_ctg = Category.objects.get(pk=ctg_id, user_id=request.user)
    all_oper = Balance.objects.filter(user_id=request.user, category_id=ctg_id).all()
    all_sum = sum([oper.sum for oper in all_oper])
    if del_ctg.dr_cr:
        new_balance = float(user_balance) + float(all_sum)
    else:
        new_balance = float(user_balance) - float(all_sum)
    if new_balance < 0:
        main_err = 'Balance cannot be less than 0'
        return redirect('view_categories')
    del_ctg.delete()
    user_balance = new_balance
    Account.objects.filter(user_id=request.user).update(sum=user_balance)
    return redirect('view_categories')


@login_required
def edit_category(request, ctg_id):
    edit_ctg = Category.objects.get(pk=ctg_id, user_id=request.user)
    all_trans = Balance.objects.filter(user_id=request.user, category_id=ctg_id).all()
    is_changed = False if all_trans else True
    if request.method == 'POST':
        try:
            dr_cr_switch = request.POST.get('switch-category')
            form = CategoryForm(request.POST)
            edit_ctg.name = request.POST.get('name')
            if dr_cr_switch is None:
                edit_ctg.dr_cr = False
            else:
                edit_ctg.dr_cr = True
            edit_ctg.save()
            return redirect(to='view_categories')
        except IntegrityError as err:
            return render(request, 'financeapp/edit_category.html',
                          {'form': CategoryForm(), 'error': 'Category will be unique!', 'category': edit_ctg,
                           'is_changed': is_changed})
    return render(request, 'financeapp/edit_category.html',
                  {'form': CategoryForm(), 'category': edit_ctg, 'is_changed': is_changed})


@login_required
def new_transaction(request, type_trans):
    global user_balance, main_err
    categories = Category.objects.filter(user_id=request.user, dr_cr=type_trans).all()
    if not categories:
        main_err = 'Enter the category first!'
        return redirect('main')
    if request.method == 'POST':
        try:
            list_categories = request.POST.getlist('categories')
            form = BalanceForm(request.POST)
            new_trans = form.save(commit=False)
            if new_trans.sum <= 0:
                raise ValueError('Sum must be greater than 0')
            if type_trans:
                new_balance = float(user_balance) - float(new_trans.sum)
            else:
                new_balance = float(user_balance) + float(new_trans.sum)
            print(new_balance)
            if new_balance < 0:
                raise ValueError('Balance cannot be less than 0')
            user_balance = new_balance
            Account.objects.filter(user_id=request.user).update(sum=user_balance)
            new_trans.user_id = request.user
            new_trans.category = Category.objects.filter(name__in=list_categories, user_id=request.user).first()
            new_trans.save()
            return redirect(to='main')
        except ValueError as err:
            return render(request, 'financeapp/transaction.html',
                          {"categories": categories, 'form': BalanceForm(), 'error': err})
    return render(request, 'financeapp/transaction.html', {"categories": categories, 'form': BalanceForm()})


@login_required
def edit_transaction(request, trans_id):
    global user_balance
    edit_trans = Balance.objects.get(pk=trans_id, user_id=request.user)
    categories = Category.objects.filter(user_id=request.user, dr_cr=edit_trans.category.dr_cr).all()
    type_trans = edit_trans.category.dr_cr
    old_sum = edit_trans.sum
    if request.method == 'POST':
        try:
            list_categories = request.POST.getlist('categories')
            new_sum = float(request.POST.get('sum'))
            if new_sum <= 0:
                raise ValueError('Sum must be greater than 0')
            if type_trans:
                new_balance = float(user_balance) + float(edit_trans.sum) - float(new_sum)
            else:
                new_balance = float(user_balance) - float(edit_trans.sum) + float(new_sum)
            print(new_balance)
            if new_balance < 0:
                raise ValueError('Balance cannot be less than 0')
            user_balance = new_balance
            Account.objects.filter(user_id=request.user).update(sum=user_balance)
            edit_trans.category = Category.objects.filter(name__in=list_categories, user_id=request.user).first()
            edit_trans.sum = new_sum
            edit_trans.save()
            return redirect(to='main')
        except ValueError as err:
            return render(request, 'financeapp/edit_transaction.html',
                          {"categories": categories, 'error': err, 'trans': edit_trans})
    return render(request, 'financeapp/edit_transaction.html',
                  {"categories": categories, 'trans': edit_trans})


@login_required
def del_transaction(request, trans_id):
    global user_balance, main_err
    del_trans = Balance.objects.get(pk=trans_id, user_id=request.user)
    if del_trans.category.dr_cr:
        new_balance = float(user_balance) + float(del_trans.sum)
    else:
        new_balance = float(user_balance) - float(del_trans.sum)
    if new_balance < 0:
        main_err = 'Balance cannot be less than 0'
        return redirect('main')
    del_trans.delete()
    user_balance = new_balance
    Account.objects.filter(user_id=request.user).update(sum=user_balance)
    return redirect('main')


@login_required
def period_search(request):
    global date_start, date_end
    today = datetime.now().date()
    if date_end is None:
        date_end = today
    if date_start is None:
        date_start = date(today.year, today.month, 1)
    if request.method == 'POST':
        try:
            selected_dates = request.POST.get('find_dates')
            if selected_dates == 'alltime':
                date_start, date_end = None, None
                return redirect(to='main')
            date1 = request.POST.get('date1')
            date2 = request.POST.get('date2')
            date_start = datetime.strptime(date1, '%Y-%m-%d').date()
            date_end = datetime.strptime(date2, '%Y-%m-%d').date()
            return redirect(to='main')
        except ValueError as err:
            return render(request, 'financeapp/period_search.html',
                          {'date1': date_start, 'date2': date_end, 'error': err})
    return render(request, 'financeapp/period_search.html', {'date1': date_start, 'date2': date_end})

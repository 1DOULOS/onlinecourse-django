from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Course, Enrollment, Question, Choice, Submission


def get_course_list(request, course_id=None):
    context = {}
    if request.user.is_authenticated:
        courses = Course.objects.filter(users=request.user)
        for course in courses:
            if course.id == course_id:
                course.is_enrolled = True
        context['course_list'] = courses
    else:
        context['course_list'] = Course.objects.all()
    return render(request, 'onlinecourse/course_list_bootstrap.html', context)


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    if user.is_authenticated:
        if not Enrollment.objects.filter(user=user, course=course).exists():
            Enrollment.objects.create(user=user, course=course, mode='honor')
            course.total_enrollment += 1
            course.save()
    return HttpResponseRedirect(reverse('onlinecourse:course_details', args=(course.id,)))


def course_details(request, course_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    context['course'] = course
    if request.user.is_authenticated:
        context['is_enrolled'] = Enrollment.objects.filter(
            user=request.user, course=course
        ).exists()
    return render(request, 'onlinecourse/course_details_bootstrap.html', context)


def loginrequest(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('onlinecourse:index'))
        else:
            context['message'] = "Invalid username or password."
    return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logoutrequest(request):
    logout(request)
    return HttpResponseRedirect(reverse('onlinecourse:index'))


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
            )
            login(request, user)
            return HttpResponseRedirect(reverse('onlinecourse:index'))
        else:
            context['message'] = "User already exists."
    return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def submit(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    enrollment = Enrollment.objects.get(user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    choices = []
    for key, value in request.POST.items():
        if key.startswith('choice'):
            choice_id = int(value)
            choices.append(choice_id)
    for choice_id in choices:
        submission.choices.add(choice_id)
    submission.save()
    return HttpResponseRedirect(reverse('onlinecourse:show_exam_result', args=(course_id, submission.id)))


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    selected_ids = list(submission.choices.values_list('id', flat=True))
    questions = course.question_set.all()
    total_score = 0
    question_results = []
    for question in questions:
        got_score = question.is_get_score(selected_ids)
        if got_score:
            total_score += question.grade
        question_results.append({
            'question': question,
            'got_score': got_score,
            'choices': [
                {
                    'choice': c,
                    'selected': c.id in selected_ids,
                }
                for c in question.choice_set.all()
            ]
        })
    context = {
        'course': course,
        'submission': submission,
        'selected_ids': selected_ids,
        'question_results': question_results,
        'total_score': total_score,
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)

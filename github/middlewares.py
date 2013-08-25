from django.contrib.auth import authenticate, login
from github.models import Authentication, User


class GithubAuthorizationMiddleware(object):
    def process_request(self, request):
        if request.GET.get('code') and request.GET.get('state'):
            auth = Authentication.objects.get(pk=request.GET.get('state'))
            access_token = auth.get_access_token(request.GET['code'])
            user = auth.application.request('user', headers={
                'Authorization': 'token %s' % access_token
            })

            github_user, created = User.objects.get_or_create(
                application=auth.application,
                uid=user['id'],
                defaults={
                    'login': user['login'],
                    'url': user['url'],
                    'email': user['email'],
                    'access_token': access_token
                }
            )
            if not created:
                github_user.access_token = access_token
                github_user.save()

            authenticated_user = authenticate(github_user=github_user)
            if not authenticated_user is None:
                if github_user.user is None:
                    github_user.user = authenticated_user
                login(request, authenticated_user)
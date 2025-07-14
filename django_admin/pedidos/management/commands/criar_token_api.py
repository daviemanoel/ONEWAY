from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria um token de API para comunicação entre Node.js e Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='api_nodejs',
            help='Nome de usuário para o token da API'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        # Criar ou buscar usuário
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Usuário "{username}" criado com sucesso.')
            )
        
        # Criar ou buscar token
        token, token_created = Token.objects.get_or_create(user=user)
        
        if token_created:
            self.stdout.write(
                self.style.SUCCESS('Token criado com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Token já existia.')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nToken de API: {token.key}')
        )
        self.stdout.write(
            self.style.WARNING('\nGuarde este token com segurança! Use-o no header:')
        )
        self.stdout.write(
            f'Authorization: Token {token.key}'
        )
import os
import re
import sys
import argparse
import textwrap

description = textwrap.dedent("""
------------------------------------------------------------------------------------------------
- If <create_backup> set to True, 
  the script will create backup at heroku using 
    'heroku pg:backups:capture --app <app_name>' 
  then download the backup using 
    'heroku pg:backups:download --app <app_name>'.
- If <create_container> set to True, 
  the script will run 
    'docker run --name <container_name> \\
        -e POSTGRES_DB=<db_name> \\
        -e POSTGRES_USER=<db_user> \\
        -e POSTGRES_PASSWORD=<db_password> \\
        -p <port>:5432 \\ 
        -v <data_directory>:/var/lib/postgresql/data \\ 
- If <import_data> set to True, 
  the script will rum
    'pg_restore --verbose --clean --no-acl --no-owner \\
        -h <host> -p <port> -U <db_user> -d <db_name> <dump_file>'.
------------------------------------------------------------------------------------------------
""")

epilog = textwrap.dedent("""
------------------------------------------------------------------------------------------------
After executing this script, you have to go to your settings.py to change your database.
In settings.py, change 
DATABASES = {
    'default': {
        'ENGINE': 'django_db_geventpool.backends.postgresql_psycopg2',
        'NAME': "<db_name>",
        'USER': "<db_user>",
        'PASSWORD': "<db_password>"
        'HOST': 'localhost',
        'PORT': '<port>',
        'CONN_MAX_AGE': 0,  # Optionally set connection max age
        'OPTIONS': {
            'MAX_CONNS': 120,  # Adjust based on your needs
        },
    },
}
                         
Reference:
- Heroku: https://devcenter.heroku.com/articles/heroku-postgres-import-export
- Postgres Docker: https://www.docker.com/blog/how-to-use-the-postgres-docker-official-image/
------------------------------------------------------------------------------------------------
""")

# Reference: 
# - Heroku: https://devcenter.heroku.com/articles/heroku-postgres-import-export
# - Postgres Docker: https://www.docker.com/blog/how-to-use-the-postgres-docker-official-image/

parser = argparse.ArgumentParser(
    description=description,
    epilog=epilog,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
def init_args():
    parser.add_argument(
        "--app_name",
        default="test",
        help="Heroku App Name. Default: 'test'",
        type=str
    )
    parser.add_argument(
        "--container_name",
        default="test",
        help="Container Name. Default: 'test'",
        type=str
    )
    parser.add_argument(
        "--postgres_version",
        help="Container Name.",
        type=str
    )
    parser.add_argument(
        "--db_name",
        default="postgres",
        help="Database Name. Default: 'postgres'",
        type=str
    )
    parser.add_argument(
        "--db_user",
        default="postgres",
        help="Database User Name. Default: 'postgres'",
        type=str
    )
    parser.add_argument(
        "--db_password",
        default="postgres",
        help="Database Password. Default: 'postgres'",
        type=str
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host that postgres run at. Default: 'localhost'",
        type=str
    )
    parser.add_argument(
        "--port",
        default=5432,
        help="Connect port from your computer to docker port:5432. Default: 5432",
        type=int
    )
    parser.add_argument(
        "--data_directory",
        default=f"{os.getcwd()}/pgdata",
        help="Directory on your host computer to store of postgres, please use absolute path or stay default. Default: '$cwd/pgdata'",
        type=str
    )
    parser.add_argument(
        "--dump_file",
        default="latest.dump",
        help="Filename to dump to postgres. Defalut: 'latest.dump'",
        type=str
    )
    parser.add_argument(
        "--create_backup",
        default=False,
        help="Create backup data at Heroku. Default: False",
        type=bool
    )
    parser.add_argument(
        "--download_backup",
        default=False,
        help="Downloaad backup data from Heroku. Default: False",
        type=bool
    )
    parser.add_argument(
        "--create_container",
        default=False,
        help="Create docker container of postgres. Default: False",
        type=bool
    )
    parser.add_argument(
        "--import_data",
        default=False,
        help="Import data to postgres. Default: False",
        type=bool
    )

def get_postgres_version(args):
    heroku_information = os.popen(f"heroku pg:info --app {args.app_name}").read()

    match = re.search("PG Version", heroku_information, flags=re.MULTILINE)
    start, stop = match.span()
    start_line = heroku_information[:start].count('\n')

    postgres_version = heroku_information.split('\n')[start_line].split(',')[0].split(' ')[-1]
    return postgres_version

def create_docker_container(args):
    postgres_version = None
    if not args.postgres_version:
        postgres_version = get_postgres_version(args)
    postgres_version = args.postgres_version
    os.system(f"docker pull postgres:{postgres_version}")
    os.system(f"docker run --name {args.container_name} -e POSTGRES_DB={args.db_name} -e POSTGRES_USER={args.db_user} -e POSTGRES_PASSWORD={args.db_password} -p {args.port}:5432 -v {args.data_directory}:/var/lib/postgresql/data -d postgres:{postgres_version}")

def import_data_to_postgres(args):
    os.system(f"pg_restore --verbose --clean --no-acl --no-owner -h {args.host} -p {args.port} -U {args.db_user} -d {args.db_name} {args.dump_file}")


def main():
    init_args()
    args = parser.parse_args()

    if args.create_backup:
        os.system(f"heroku pg:backups:capture --app {args.app_name}")
        os.system(f"heroku pg:backups:download --app {args.app_name}")
        args.dump_file = "latest.dump"
    elif args.download_backup:
        os.system(f"heroku pg:backups:download --app {args.app_name}")
        args.dump_file = "latest.dump"
    
    if args.create_container:
        create_docker_container(args)
    
    if args.import_data:
        import_data_to_postgres(args)

main()









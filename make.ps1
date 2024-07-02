# PowerShell script to replicate Make functionality on Windows
# VERSION = 2024.07.01

param (
    [Parameter(Mandatory = $true, Position = 0)]
    [ArgumentCompletions(
        'help', 'pip-tools', 'sync', 'requirements', 'upgrade', 'migrations', 'migrate', 'urls', 'build', 'app', 'bash',
        'shell', 'dev', 'dev-http', 'test', 'clean', 'env', 'superuser', 'janitor', 'dumpdata', 'loaddata', 'push'
    )]
    [string]$Command,

    [Parameter(Position = 1, ValueFromRemainingArguments)]
    [string]$Arguments
)

$dc = "docker-compose"
$run = "$dc run --rm -u 0:0"
$manage = "$run dev python manage.py"
$pytest = "$run test pytest $ARGS"
$pip_compile = "pip-compile --allow-unsafe --strip-extras --resolver=backtracking --quiet"

$build_version = (git describe --tags --exact-match 2> $null || git symbolic-ref -q --short HEAD)
$build_revision = (git rev-parse --short HEAD)
$build_date = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")

function help {
    $helpText = @"
help             Show this help.
init             Start with a clean docker workload.
pip-tools        Install pip-tools.
sync             Sync your local venv with expected state as defined in requirements.txt.
requirements     (Re)compile requirements.txt and requirements_dev.txt.
upgrade          Upgrade the requirements.txt files, adhering to the constraints in the requirements.in files.
migrations       Make migrations.
migrate          Migrate.
urls             Show URLs.
build            Build docker image.
app              Run app.
bash             Run the container and start bash.
shell            Run a Django shell.
dev              Run the development app over SSL with runserver_plus.
dev-http         Run the development app over plain http with runserver.
test             Execute tests. Optionally use an argument to define which specific test(s), i.e.: make test app.class.function
clean            Clean docker stuff.
env              Print current env.
superuser        Create a superuser (user with admin rights).
janitor          Run the janitor.
dumpdata         Create a json dump. Optionally use arguments to define which tables, i.e.: make dumpdata app app2.model.
loaddata         Load fixtures. User arguments to load multiple fixtures, i.e.: make loaddata fixture1 fixture2.json
push             Push to container registry.

make             Call this script with make as an alias by setting: Set-Alias -Name make -Value '.\make.ps1'
"@
    Write-Host $helpText
}

switch ($Command) {
    "help" {
        help
    }
    "init" {
        .\Make.ps1 clean
        .\Make.ps1 build
        .\Make.ps1 migrate
    }
    "pip-tools" {
        pip install pip-tools
    }
    "sync" {
        pip install pip-tools
        pip-sync requirements.txt requirements_dev.txt
    }
    "requirements" {
        pip install pip-tools
        Invoke-Expression "$pip_compile requirements.in"
        Invoke-Expression "$pip_compile requirements_dev.in"
    }
    "upgrade" {
        Invoke-Expression "$pip_compile --upgrade requirements.in"
        Invoke-Expression "$pip_compile --upgrade requirements_dev.in"
    }
    "migrations" {
        Invoke-Expression "$manage makemigrations"
    }
    "migrate" {
        Invoke-Expression "$manage migrate"
    }
    "urls" {
        Invoke-Expression "$manage show_urls"
    }
    "build" {
        $env:BUILD_DATE = $build_date
        $env:BUILD_REVISION = $build_revision
        $env:BUILD_VERSION = $build_version
        Invoke-Expression "$dc build"
    }
    "app" {
        Invoke-Expression "$run --service-ports app"
    }
    "bash" {
        Invoke-Expression "$run dev bash"
    }
    "shell" {
        Invoke-Expression "$manage shell"
    }
    "dev" {
        Invoke-Expression "$run --service-ports dev python manage.py runserver_plus 0.0.0.0:8000 --cert-file cert.crt --key-file cert.key"
    }
    "dev-http" {
        Invoke-Expression "$run --service-ports dev python manage.py runserver 0.0.0.0:8000"
    }
    "test" {
        if ($Arguments) {
            Invoke-Expression "$manage test $Arguments"            
        }
        else {
            Invoke-Expression "$manage test"
        }
    }
    "clean" {
        Invoke-Expression "$dc down -v --remove-orphans"
    }
    "env" {
        Invoke-Expression "$run dev env | Sort-Object"
    }
    "superuser" {
        Invoke-Expression "$manage createsuperuser"
    }
    "janitor" {
        Invoke-Expression "$manage janitor"
    }
    "dumpdata" {
        Invoke-Expression "$run dev bash -c './manage.py dumpdata -a --indent 2 --format=json $Arguments> dump.json'"
    }
    "loaddata" {
        if ($Arguments) {
            $fixtures = $Arguments -join ' '
        }
        else {
            $fixtures = "locations location_properties property_options location_data external_services location_external_services location_docs property_groups"
        }
        Invoke-Expression "$manage loaddata $fixtures"
    }
    "push" {
        Invoke-Expression "$dc push"
    }
    default {
        Write-Host "Invalid command. Use 'help' to see available commands."
    }
}
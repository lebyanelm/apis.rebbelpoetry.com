# dependencies


# -> Creates files directories from a path that are missing
def resolve_directory_path(path: str) -> None:
    path_split = path.split('/')
    current_path = ''

    for file in path_split:
        if file == '':
            current_path = '/'
        else:
            current_path = '/'.join([current_path, file])
        if os.path.exists(current_path) == False:
            os.mkdir(current_path)

    return True


# -> Takes in a resource file path and returns a remote URL for external devices
def generate_resource_url(resource_path: str) -> str:
    # -> get the starting point of the source code directory to find uploads path
    strip_path = f'{os.getcwd()}/uploads/'
    half_resource_path = resource_path.split(strip_path)[1]

    # -> return the correct resource URL according to the environment of the source code
    if os.environ['PROD'] == os.environ['PRODUCTION_MODE']:
        return '/'.join([os.environ['PROD_UPLOADS'], half_resource_path])
    else:
        return '/'.join([os.environ['DEV_UPLOADS'], half_resource_path])
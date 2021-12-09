# dependencies
import os
import nanoid


# -> Creates files directories from a path that are missing
def resolve_directory_path(path: str) -> None:
    path_split = path.split("/")
    current_path = ""

    for file in path_split:
        if file == "":
            current_path = "/"
        else:
            current_path = "/".join([current_path, file])
        if os.path.exists(current_path) == False:
            os.mkdir(current_path)

    return True


# -> Takes in a resource file path and returns a remote URL for external devices
def generate_resource_urls(resource_path: str, extension, is_audio=False) -> str:
    # -> get the starting point of the source code directory to find uploads path
    strip_path = f"{os.getcwd()}/uploads/"
    half_resource_path = resource_path.split(strip_path)[1]

    # -> return the correct resource URL according to the environment of the source code
    if os.environ.get("PRODUCTION_ENVIRONMENT"):
        uploads_url = "/".join([os.environ["PROD_UPLOADS"], half_resource_path])
    else:
        uploads_url = "/".join([os.environ["DEV_UPLOADS"], half_resource_path])

    if is_audio == False:
        resource = dict(
            large="/".join([uploads_url, "large." + extension]),
            medium="/".join([uploads_url, "medium." + extension]),
            small="/".join([uploads_url, "small." + extension]))
    else:
        resource = dict(original="/".join([uploads_url, "original." + extension]))

    return resource


def generate_filename() -> str:
    return nanoid.generate(size=30)


def get_file_extension(filename: str) -> str:
    print(filename, filename.rsplit("."), filename.rsplit(".")[-1])
    return filename.rsplit(".")[-1]
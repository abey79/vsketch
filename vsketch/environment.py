try:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import google.colab
    import requests

    COLAB = True
except ModuleNotFoundError:
    COLAB = False

try:
    # noinspection PyPackageRequirements
    import IPython
except ModuleNotFoundError:
    pass

try:
    # noinspection PyUnresolvedReferences
    JUPYTERLAB = get_ipython().__class__.__name__ == "ZMQInteractiveShell"  # type: ignore
except NameError:
    JUPYTERLAB = False

SVG_PAN_ZOOM_LIB = "http://ariutta.github.io/svg-pan-zoom/dist/svg-pan-zoom.min.js"
SVG_PAN_ZOOM_ROOT = "/usr/local/share/jupyter"
SVG_PAN_ZOOM_DEST = "/nbextensions/google.colab/svg-pan-zoom.min.js"


def get_svg_pan_zoom_url() -> str:
    """Returns the URL of the svg-pan-zoom JS library, which depends on the actual environment
    since it must first be locally copied with Google Colab.
    """
    if COLAB:
        return SVG_PAN_ZOOM_DEST
    else:
        return SVG_PAN_ZOOM_LIB


def setup_colab() -> None:
    if "IPython" not in globals() or "requests" not in globals():
        raise RuntimeError(
            "IPython and requests packages are required when setting up for Google Colab"
        )
    r = requests.get(SVG_PAN_ZOOM_LIB, allow_redirects=True)
    with open(SVG_PAN_ZOOM_ROOT + SVG_PAN_ZOOM_DEST, "wb") as fp:
        fp.write(r.content)


def setup() -> None:
    if COLAB:
        setup_colab()

    if COLAB or JUPYTERLAB:
        IPython.display.set_matplotlib_formats("svg")

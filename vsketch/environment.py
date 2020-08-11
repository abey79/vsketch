try:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import google.colab

    COLAB = True
except ModuleNotFoundError:
    COLAB = False

try:
    # noinspection PyPackageRequirements
    import IPython
    import requests
except ModuleNotFoundError:
    pass


SVG_PAN_ZOOM_LIB = "http://ariutta.github.io/svg-pan-zoom/dist/svg-pan-zoom.min.js"
SVG_PAN_ZOOM_ROOT = "/usr/local/share/jupyter"
SVG_PAN_ZOOM_DEST = "/nbextensions/google.colab/svg-pan-zoom.min.js"


def setup_colab() -> None:
    if "IPython" not in globals() or "requests" not in globals():
        raise RuntimeError(
            "IPython and requests packages are required when setting up for Google Colab"
        )
    r = requests.get(SVG_PAN_ZOOM_LIB, allow_redirects=True)
    with open(SVG_PAN_ZOOM_ROOT + SVG_PAN_ZOOM_DEST, "wb") as fp:
        fp.write(r.content)
    # noinspection PyUnresolvedReferences
    IPython.display.display_html(f"<script src='{SVG_PAN_ZOOM_DEST}'></script>", raw=True)


def setup() -> None:
    if COLAB:
        setup_colab()

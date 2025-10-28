def test_routes_exist():
    from importlib import import_module
    app = import_module("app.main").app
    paths = [r.path for r in app.router.routes]
    assert "/healthz" in paths
    assert "/measurements" in paths

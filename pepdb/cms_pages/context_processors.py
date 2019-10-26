def get_site_root(request):
    # NB this returns a core.Page, not the implementation-specific model used
    # so object-comparison to self will return false as objects would differ
    return request.site.root_page.homepage


def has_menu_children(page):
    return page.get_children().live().in_menu().exists()


def menu_processor(request):
    root_page = get_site_root(request)

    return {
        "root_page": root_page
    }

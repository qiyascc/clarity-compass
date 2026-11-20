from clarity_worker.discovery import Frontier


def drain(frontier: Frontier, limit: int = 100) -> list[str]:
    urls: list[str] = []
    while len(urls) < limit and (item := frontier.pop()) is not None:
        urls.append(item.url)
    return urls


def test_pops_breadth_first_and_respects_page_limit() -> None:
    frontier = Frontier("https://shop.test/", max_pages=3, max_depth=5)
    frontier.add_links("https://shop.test/", ["/a", "/b", "/c"])
    assert drain(frontier) == [
        "https://shop.test/",
        "https://shop.test/a",
        "https://shop.test/b",
    ]


def test_ignores_foreign_hosts_fragments_and_files() -> None:
    frontier = Frontier("https://shop.test/", max_pages=50, max_depth=5)
    frontier.pop()
    frontier.add_links(
        "https://shop.test/",
        [
            "https://other.test/x",
            "mailto:hi@shop.test",
            "javascript:void(0)",
            "/brochure.pdf",
            "/a#top",
            "/a",
            "https://www.shop.test/b",
        ],
    )
    assert drain(frontier) == ["https://shop.test/a", "https://www.shop.test/b"]


def test_depth_limit() -> None:
    frontier = Frontier("https://shop.test/", max_pages=50, max_depth=1)
    root = frontier.pop()
    assert root is not None
    frontier.add_links(root.url, ["/level1"])
    child = frontier.pop()
    assert child is not None
    assert child.depth == 1
    frontier.add_links(child.url, ["/level2"])
    assert frontier.pop() is None


def test_exclude_patterns() -> None:
    frontier = Frontier("https://shop.test/", max_pages=50, max_depth=3, exclude=["/admin/*"])
    frontier.pop()
    frontier.add_links("https://shop.test/", ["/admin/users", "/about"])
    item = frontier.pop()
    assert item is not None
    assert item.url == "https://shop.test/about"
    assert frontier.pop() is None


def test_key_pages_jump_the_queue() -> None:
    frontier = Frontier("https://shop.test/", max_pages=50, max_depth=3)
    frontier.pop()
    frontier.add_links("https://shop.test/", ["/blog/1", "/blog/2", "/contact", "/login"])
    assert drain(frontier, 2) == [
        "https://shop.test/contact",
        "https://shop.test/login",
    ]


def test_redirected_host_is_adopted() -> None:
    frontier = Frontier("https://old.test/", max_pages=10, max_depth=2)
    frontier.pop()
    frontier.adopt_host("https://new.test/")
    frontier.add_links("https://new.test/", ["/about"])
    item = frontier.pop()
    assert item is not None
    assert item.url == "https://new.test/about"


def test_seeds_are_depth_zero() -> None:
    frontier = Frontier("https://shop.test/", max_pages=10, max_depth=0)
    frontier.add_seeds(["https://shop.test/pricing"])
    assert drain(frontier, 2) == [
        "https://shop.test/",
        "https://shop.test/pricing",
    ]


def test_redirect_target_is_not_visited_twice() -> None:
    frontier = Frontier("https://old.test/", max_pages=10, max_depth=2)
    frontier.pop()
    frontier.adopt_host("https://new.test/")
    frontier.mark_visited("https://new.test/")
    frontier.add_links("https://new.test/", ["/", "/about"])
    assert drain(frontier) == ["https://new.test/about"]

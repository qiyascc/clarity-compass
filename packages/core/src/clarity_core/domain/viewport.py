from enum import StrEnum


class Viewport(StrEnum):
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"

    @property
    def width(self) -> int:
        return _SIZES[self][0]

    @property
    def height(self) -> int:
        return _SIZES[self][1]

    @property
    def is_mobile(self) -> bool:
        return self is not Viewport.DESKTOP

    @property
    def scale(self) -> float:
        return 1.0 if self is Viewport.DESKTOP else 2.0


_SIZES = {
    Viewport.DESKTOP: (1440, 900),
    Viewport.TABLET: (834, 1112),
    Viewport.MOBILE: (390, 844),
}

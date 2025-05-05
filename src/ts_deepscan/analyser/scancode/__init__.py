import typing as t
import functools
import warnings

from time import time


def detect_copyrights(text: str,
                      copyrights=True, holders=True, authors=True,
                      include_years=True, include_allrights=False,
                      timeout=-1):
    from cluecode.copyrights import Detection, detect_copyrights_from_lines
    from scancode.interrupt import interruptible

    numbered_lines = list(enumerate(text.splitlines()))

    detect = functools.partial(detect_copyrights_from_lines,
                               numbered_lines=numbered_lines,
                               include_copyrights=copyrights,
                               include_holders=holders,
                               include_authors=authors,
                               include_copyright_years=include_years,
                               include_copyright_allrights=include_allrights)
    if timeout > 0:
        detect = functools.partial(detect, deadline=time() + int(timeout / 2.5))
        _, detections = interruptible(detect, timeout=timeout)
    else:
        detections = detect()

    copyrights, holders, authors = Detection.split(detections)

    for v in copyrights:
        yield 'copyrights', v.copyright, v.start_line, v.end_line

    for v in holders:
        yield 'holders', v.holder, v.start_line, v.end_line

    for v in authors:
        yield 'authors', v.author, v.start_line, v.end_line


def detect_licenses(text: str,
                    include_text: bool = False,
                    timeout=-1) -> t.Tuple[list, list, t.Optional[str]]:

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        from licensedcode.detection import detect_licenses
        from licensedcode.cache import build_spdx_license_expression, get_cache
        from packagedcode.utils import combine_expressions
        from scancode.interrupt import interruptible

    detect = functools.partial(detect_licenses,
                               query_string=text,
                               include_text=include_text)

    if timeout > 0:
        detect = functools.partial(detect, deadline=time() + int(timeout / 2.5))
        _, detections = interruptible(detect, timeout=timeout)
    else:
        detections = detect()

    lic_detections = []
    lic_expressions = []
    lic_expressions_spdx = None
    lic_clues = []

    for d in detections:
        d_dict = d.to_dict(
            include_text=include_text
        )

        if expr := d.license_expression:
            lic_expressions.append(expr)
            lic_detections.append(d_dict)
        else:
            lic_clues.extend(d_dict["matches"])

    if lic_expressions:
        lic_expressions = combine_expressions(
            expressions=lic_expressions,
            relation='AND',
            unique=True,
        )
        lic_expressions_spdx = str(build_spdx_license_expression(
            lic_expressions,
            licensing=get_cache().licensing
        ))

    return lic_detections, lic_clues, lic_expressions_spdx

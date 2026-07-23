"""
ExtractStep — fetch media metadata using the registered extractor.
"""

import tetodl.extractors  # noqa: F401 — auto-registers extractors
from tetodl.utils.tracer import trace, traced

from ...core.extractor import resolve_extractor
from ...core.models import PipelineContext
from ...core.step import PipelineError, PipelineStep


class ExtractStep(PipelineStep[PipelineContext, PipelineContext]):
    """Extract metadata from a URL using the registered extractor plugin.

    Uses :func:`resolve_extractor` to find a matching extractor for
    ``ctx.url``, then calls ``extractor.extract()`` to produce a
    :class:`MediaInfo`.

    See Also
    --------
    :func:`resolve_extractor` : Extractor resolution logic.
    :class:`MediaInfo` : Extracted metadata model.
    :class:`ClassifyStep` : Next step in the pipeline.

    Example
    -------
    >>> from tetodl.core.models import PipelineContext
    >>> step = ExtractStep()
    >>> ctx = PipelineContext(url="https://youtube.com/watch?v=example")
    >>> result = step(ctx)
    """

    @trace
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        """Extract metadata for the URL in the pipeline context.

        Parameters
        ----------
        ctx : PipelineContext
            Pipeline context with ``url`` set.

        Returns
        -------
        PipelineContext
            Context with ``media_info`` set, or ``error`` set on failure.

        Raises
        ------
        PipelineError
            Propagated from :func:`resolve_extractor` when no matching
            extractor is found, or from the extractor plugin when the
            extraction request fails.

        See Also
        --------
        :func:`resolve_extractor` : Extractor resolution.
        :class:`PipelineError` : Error model for pipeline failures.

        Example
        -------
        >>> step = ExtractStep()
        >>> ctx = PipelineContext(url="https://youtube.com/watch?v=example")
        >>> result = step(ctx)
        >>> result.media_info is not None or result.error is not None
        True
        """
        try:
            extractor = resolve_extractor(ctx.url)
        except PipelineError as exc:
            ctx.error = str(exc)
            return ctx

        try:
            ctx.media_info = extractor.extract(ctx.url)
        except PipelineError as exc:
            with traced(f'extract failed — {exc}'):
                ctx.error = str(exc)

        return ctx

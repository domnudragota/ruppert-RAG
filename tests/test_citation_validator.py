from ruppert.citation_validator import validate_citations

ALLOWED_SOURCES = (
    "workflow.md:L10-20",
    "workflow.md:L21-30",
)


def test_valid_citations():
    answer = (
        "We test behavior [workflow.md:L10-20] and regressions [workflow.md:L21-30]."
    )

    report = validate_citations(answer, ALLOWED_SOURCES)

    assert report.passed
    assert len(report.valid) == 2
    assert report.invalid == ()


def test_rejects_invented_citations():
    answer = "Testing [1:L10-20]. Regression [workflow.md:L10-30]."

    report = validate_citations(answer, ALLOWED_SOURCES)

    assert not report.passed
    assert len(report.invalid) == 2
    assert report.valid == ()


def test_detects_missing_citations():
    answer = "We should test regressions."

    report = validate_citations(answer, ALLOWED_SOURCES)

    assert report.missing
    assert not report.passed


def test_mixed_valid_and_invalid_citations():
    answer = "Verified [workflow.md:L10-20]. Unverified [other.md:L50-60]."

    report = validate_citations(answer, ALLOWED_SOURCES)

    assert report.valid == ("workflow.md:L10-20",)
    assert report.invalid == ("other.md:L50-60",)
    assert not report.passed


def test_accepts_backtick_formatted_citations():
    answer = "Testing `workflow.md:L10-20` and regression `workflow.md:L21-30`."

    report = validate_citations(answer, ALLOWED_SOURCES)

    assert report.passed
    assert report.valid == ALLOWED_SOURCES
    assert report.invalid == ()


def test_rejects_partial_line_reference():
    answer = "Valid source `workflow.md:L10-20`. Unverified line `workflow.md:L25`."

    report = validate_citations(answer, ALLOWED_SOURCES)

    assert report.valid == ("workflow.md:L10-20",)
    assert report.invalid == ("workflow.md:L25",)
    assert not report.passed


def test_deduplicates_citations_across_formats():
    answer = "First [workflow.md:L10-20]. Repeated `workflow.md:L10-20`."

    report = validate_citations(answer, ALLOWED_SOURCES)

    assert report.passed
    assert report.valid == ("workflow.md:L10-20",)


def test_accepts_markdown_source_link_with_exact_range():
    answer = "[Testing](source:workflow.md:L10-20)."

    report = validate_citations(answer, ALLOWED_SOURCES)

    assert report.passed
    assert report.valid == ("workflow.md:L10-20",)
    assert report.invalid == ()


def test_detects_markdown_links_with_invented_ranges():
    answer = (
        "First [Task](source:workflow.md:L10). "
        "Second [Task](source:workflow.md:L21-L30)."
    )

    report = validate_citations(answer, ALLOWED_SOURCES)

    assert report.valid == ()
    assert report.invalid == (
        "workflow.md:L10",
        "workflow.md:L21-L30",
    )
    assert not report.missing
    assert not report.passed

from datetime import date

from lead_finder.rotation import load_queries, slice_for_day


def test_load_queries_ignores_comments_and_blanks():
    text = "# header\n\nsite:linkedin.com \"a\" \"b\"\n  \nsite:linkedin.com \"c\" \"d\"\n"
    assert load_queries(text) == [
        'site:linkedin.com "a" "b"',
        'site:linkedin.com "c" "d"',
    ]


def test_slice_size_bounded_by_list_length():
    queries = ["q1", "q2", "q3"]
    result = slice_for_day(queries, slice_size=10, day=date(2026, 1, 1))
    assert result == queries  # can't slice more than exist


def test_slices_advance_by_day():
    queries = [f"q{i}" for i in range(10)]
    d1 = slice_for_day(queries, slice_size=5, day=date(2026, 1, 1))
    d2 = slice_for_day(queries, slice_size=5, day=date(2026, 1, 2))
    assert len(d1) == 5 and len(d2) == 5
    assert d1 != d2  # consecutive days run different slices


def test_full_cycle_covers_every_query():
    queries = [f"q{i}" for i in range(20)]
    slice_size = 5
    num_slices = (len(queries) + slice_size - 1) // slice_size  # 4
    covered = set()
    for offset in range(num_slices):
        day = date.fromordinal(date(2026, 1, 1).toordinal() + offset)
        covered.update(slice_for_day(queries, slice_size, day=day))
    assert covered == set(queries)


def test_empty_list_returns_empty():
    assert slice_for_day([], slice_size=5, day=date(2026, 1, 1)) == []

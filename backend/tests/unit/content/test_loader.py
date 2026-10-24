import shutil
from pathlib import Path

import pytest

from codeadapt.content import ContentError, Visibility, load_catalogue, load_problem
from tests.paths import DEMO_CONTENT, DEMO_SLUGS, ORIGINAL_SLUGS

LOWER_BOUND = DEMO_CONTENT / "lower-bound"


@pytest.fixture
def problem_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "lower-bound"
    shutil.copytree(LOWER_BOUND, dst)
    return dst


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text, old
    path.write_text(text.replace(old, new, 1))


def test_demo_problem_loads() -> None:
    problem = load_problem(LOWER_BOUND)
    spec = problem.spec
    assert spec.slug == "lower-bound"
    assert len(spec.tests) >= 12
    assert len(spec.error_models) >= 5
    assert any(t.visibility is Visibility.SAMPLE for t in spec.tests)
    assert "lower_bound_index" in problem.harness
    assert set(problem.error_model_sources) == {m.key for m in spec.error_models}
    assert len(problem.version) == 64


def test_program_bundles_solution_with_harness() -> None:
    problem = load_problem(LOWER_BOUND)
    files = problem.program("int x;")
    assert [f.name for f in files] == ["solution.cpp", "harness.cpp"]


def test_catalogue_lists_problem_directories() -> None:
    slugs = [p.spec.slug for p in load_catalogue(DEMO_CONTENT)]
    assert slugs == DEMO_SLUGS
    assert set(ORIGINAL_SLUGS) <= set(slugs)


def test_version_is_stable_and_content_addressed(problem_copy: Path) -> None:
    v1 = load_problem(problem_copy).version
    assert load_problem(problem_copy).version == v1
    (problem_copy / "error_models" / "no_progress_update.cpp").write_text("// changed\n")
    assert load_problem(problem_copy).version != v1


def test_unreferenced_files_do_not_change_version(problem_copy: Path) -> None:
    v1 = load_problem(problem_copy).version
    (problem_copy / "notes.txt").write_text("scratch")
    assert load_problem(problem_copy).version == v1


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('probes = ["empty_input"]', 'probes = ["nope"]', "unknown probe 'nope'"),
        ('key = "below_all"', 'key = "empty"', "duplicate test key 'empty'"),
        ('skill = "loop_termination"', 'skill = "nope"', "unknown skill 'nope'"),
        ('empty_input = ["search_space_boundaries"]', 'empty_input = ["x"]', "unknown skill 'x'"),
        ('visibility = "sample"', 'visibility = "hidden"', None),  # one sample remains
        ('harness = "harness.cpp"', 'harness = "../harness.cpp"', "invalid relative path"),
        ('solution_file = "solution.cpp"', 'solution_file = "harness.cpp"', "harness.cpp"),
        ('slug = "lower-bound"', 'slug = "other"', "must equal the directory name"),
        ('title = "Lower bound"', 'title = "Lower bound"\nsurprise = 1', "Extra inputs"),
        (
            'distinguishes = ["exact_match_sentinel", "returns_wrong_pointer"]',
            'distinguishes = ["nope"]',
            "distinguishes unknown error model 'nope'",
        ),
        (
            'equivalents = ["count-occurrences", "last-less-than"]',
            'equivalents = ["lower-bound"]',
            "invalid problem reference 'lower-bound'",
        ),
        ('equivalents = ["count-occurrences", "last-less-than"]', 'transfer = ["Bad"]', "'Bad'"),
    ],
)
def test_invalid_definitions_are_rejected(
    problem_copy: Path, old: str, new: str, message: str | None
) -> None:
    edit(problem_copy / "problem.toml", old, new)
    if message is None:
        load_problem(problem_copy)
        return
    with pytest.raises(ContentError, match=message):
        load_problem(problem_copy)


def test_requires_a_sample_test(problem_copy: Path) -> None:
    toml = problem_copy / "problem.toml"
    toml.write_text(toml.read_text().replace('visibility = "sample"', 'visibility = "hidden"'))
    with pytest.raises(ContentError, match="sample test is required"):
        load_problem(problem_copy)


def test_missing_file_is_reported(problem_copy: Path) -> None:
    (problem_copy / "error_models" / "no_progress_update.cpp").unlink()
    with pytest.raises(ContentError, match="missing file"):
        load_problem(problem_copy)


def test_symlink_escape_is_rejected(problem_copy: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.cpp"
    outside.write_text("int secret;")
    target = problem_copy / "error_models" / "no_progress_update.cpp"
    target.unlink()
    target.symlink_to(outside)
    with pytest.raises(ContentError, match="escapes"):
        load_problem(problem_copy)


def test_malformed_toml(problem_copy: Path) -> None:
    (problem_copy / "problem.toml").write_text("slug = ")
    with pytest.raises(ContentError, match="cannot parse"):
        load_problem(problem_copy)


def test_skills_probed_by() -> None:
    spec = load_problem(LOWER_BOUND).spec
    single = next(t for t in spec.tests if t.key == "single_above")
    assert spec.skills_probed_by(single) == {
        "search_space_boundaries",
        "loop_termination",
        "problem_specification",
    }


def test_curriculum_links_must_name_problems_in_the_catalogue(tmp_path: Path) -> None:
    catalogue = tmp_path / "bank"
    shutil.copytree(DEMO_CONTENT, catalogue)
    shutil.rmtree(catalogue / "last-less-than")
    with pytest.raises(ContentError, match=r"unknown problems \['last-less-than'\]"):
        load_catalogue(catalogue)


def test_demo_curriculum_links() -> None:
    specs = {p.spec.slug: p.spec for p in load_catalogue(DEMO_CONTENT)}
    assert specs["lower-bound"].curriculum.equivalents == ("count-occurrences", "last-less-than")
    assert specs["count-occurrences"].curriculum.prerequisites == ("lower-bound",)
    assert all(t.distinguishes is not None and t.purpose for s in specs.values() for t in s.tests)

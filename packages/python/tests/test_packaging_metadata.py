from pathlib import Path
import tomllib

def test_pyproject_metadata_sections_are_valid():
    path=Path(__file__).parents[1]/"pyproject.toml"
    with path.open("rb") as f:
        data=tomllib.load(f)
    project=data["project"]
    optional=project["optional-dependencies"]
    assert project["license"]["text"]=="Apache-2.0"
    assert isinstance(project["authors"],list)
    assert isinstance(project["keywords"],list)
    assert isinstance(project["classifiers"],list)
    for name, deps in optional.items():
        assert isinstance(deps,list), f"optional dependency group {name!r} must be an array"
        assert all(isinstance(dep,str) for dep in deps)

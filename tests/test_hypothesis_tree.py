from market_entry_toolkit.hypothesis_tree import Hypothesis, Verdict, build_case_tree


def test_build_case_tree_shape():
    tree = build_case_tree()
    assert tree.id == "0"
    assert len(tree.children) == 4
    assert [c.id for c in tree.children] == ["1", "2", "3", "4"]
    assert len(tree.leaves()) == 8


def test_find_locates_nested_node():
    tree = build_case_tree()
    node = tree.find("2.2")
    assert node is not None
    assert node.id == "2.2"
    assert tree.find("nonexistent") is None


def test_leaf_rollup_is_own_verdict():
    leaf = Hypothesis(id="x", statement="s", analysis="a")
    assert leaf.rollup_verdict() == Verdict.PENDING
    leaf.resolve("finding", Verdict.SUPPORTED)
    assert leaf.rollup_verdict() == Verdict.SUPPORTED


def test_rollup_all_supported():
    parent = Hypothesis(
        id="p",
        statement="p",
        analysis="a",
        children=[
            Hypothesis(id="c1", statement="c1", analysis="a"),
            Hypothesis(id="c2", statement="c2", analysis="a"),
        ],
    )
    parent.children[0].resolve("f", Verdict.SUPPORTED)
    parent.children[1].resolve("f", Verdict.SUPPORTED)
    assert parent.rollup_verdict() == Verdict.SUPPORTED


def test_rollup_any_not_supported_sinks_branch():
    parent = Hypothesis(
        id="p",
        statement="p",
        analysis="a",
        children=[
            Hypothesis(id="c1", statement="c1", analysis="a"),
            Hypothesis(id="c2", statement="c2", analysis="a"),
        ],
    )
    parent.children[0].resolve("f", Verdict.SUPPORTED)
    parent.children[1].resolve("f", Verdict.NOT_SUPPORTED)
    assert parent.rollup_verdict() == Verdict.NOT_SUPPORTED


def test_rollup_mixed_is_partially_supported():
    parent = Hypothesis(
        id="p",
        statement="p",
        analysis="a",
        children=[
            Hypothesis(id="c1", statement="c1", analysis="a"),
            Hypothesis(id="c2", statement="c2", analysis="a"),
        ],
    )
    parent.children[0].resolve("f", Verdict.SUPPORTED)
    parent.children[1].resolve("f", Verdict.PARTIALLY_SUPPORTED)
    assert parent.rollup_verdict() == Verdict.PARTIALLY_SUPPORTED


def test_rollup_any_pending_is_pending():
    parent = Hypothesis(
        id="p",
        statement="p",
        analysis="a",
        children=[
            Hypothesis(id="c1", statement="c1", analysis="a"),
            Hypothesis(id="c2", statement="c2", analysis="a"),
        ],
    )
    parent.children[0].resolve("f", Verdict.SUPPORTED)
    assert parent.rollup_verdict() == Verdict.PENDING


def test_branch_summary_bullets_one_per_child_no_finding_text():
    tree = build_case_tree()
    for leaf in tree.leaves():
        leaf.resolve("some finding detail", Verdict.SUPPORTED)
    bullets = tree.branch_summary_bullets()
    assert len(bullets) == 4
    for bullet in bullets:
        assert "some finding detail" not in bullet

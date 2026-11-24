from olist_pipeline.oracle import main as validate
from olist_pipeline.report import report
from olist_pipeline.run import run


def test_fresh_results_pass_validation(conn, tmp_path, fixtures):
    run(conn, (fixtures / "worked_example"))
    report(conn, tmp_path)
    assert validate(fixtures / "worked_example", tmp_path) == []


def test_a_wrong_result_fails_validation_by_name(conn, tmp_path, fixtures):
    run(conn, (fixtures / "worked_example"))
    report(conn, tmp_path)
    sales = tmp_path / "q1_sales_by_month_state.csv"
    sales.write_text(sales.read_text().replace("150.00", "151.00"), newline="")
    assert validate(fixtures / "worked_example", tmp_path) == ["sales by month and state"]

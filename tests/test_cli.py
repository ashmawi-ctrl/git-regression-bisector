from regression_bisector.cli import main


def test_cli_requires_verification_command(tmp_path, capsys) -> None:
    exit_code = main(
        [
            str(tmp_path),
            "--good",
            "HEAD~1",
            "--bad",
            "HEAD",
        ]
    )

    assert exit_code == 2
    assert "verification command" in capsys.readouterr().out

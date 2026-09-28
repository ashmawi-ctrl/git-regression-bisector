# Git Regression Bisector

A small debugging tool for locating the first commit that changes a command from passing to failing.

The project is aimed at a common maintenance problem: a test passes on an older revision, fails on a newer revision, and the useful question is not only *what is broken?* but *where did the behavior first change?*

The implementation will use Git history plus an explicit verification command, while avoiding changes to the caller's working tree.

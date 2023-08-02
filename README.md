[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Build and test using Docker](https://github.com/hartwork/wnpp.debian.net/actions/workflows/build_and_test_using_docker.yml/badge.svg)](https://github.com/hartwork/wnpp.debian.net/actions/workflows/build_and_test_using_docker.yml)


# About `wnpp.debian.net`

The [`wnpp.debian.net`](https://wnpp.debian.net/) project started out
in 2009
with spaghetti PHP 5 code and MySQL
and the goal of providing a better user experience
than already existing WNPP pages
[[1]](https://www.debian.org/devel/wnpp/being_packaged)
and
[[2]](https://www.debian.org/devel/wnpp/requested)
combined.  Judging from an e-mail from 2008, I originally intended
to better show which Debian packages…

- are potentially easy to package, therefore suitable
  for motivated Debian rookies,
- are really wanted,
- are important though harder to package, or
- are catching dust already.

Some of that I achieved with this project.

By 2021 it became clear,
that keeping old PHP and a deprecated MySQL adapter around
would need a soon replacement to not catch fire…
so I re-wrote the entire project in Django and Python 3
and replaced MySQL by PostgreSQL.
The Django database model is a direct port of the original MySQL table schema
(and hence is not ideal)
and the user interface is the same
so it still looks like the 90s.
At least the tech stack no longer is a zombie,
has enough test coverage to
allow blind updates of third party dependencies with low risk, and
has a good chance to survive for a few more years.

The code is licensed under the `GNU Affero GPL v3 or later` license.

If you like the `wnpp.debian.net` project, please support the project
by starring its [GitHub repository](https://github.com/hartwork/wnpp.debian.net).
Thank you!

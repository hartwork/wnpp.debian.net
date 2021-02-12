# Copyright (C) 2021 Sebastian Pipping <sebastian@pipping.org>
# Licensed under GNU Affero GPL v3 or later

class ReportingMixin:
    def _error(self, text: str) -> None:
        self.stderr.write(self.style.ERROR(text))

    def _notice(self, text: str) -> None:
        self.stdout.write(self.style.NOTICE(text))

    def _success(self, text: str) -> None:
        self.stdout.write(self.style.SUCCESS(text))

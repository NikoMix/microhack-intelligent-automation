#!/usr/bin/env python3
"""Generate a small, license-free sample invoice PDF for Lab 3.

Pure standard library — no third-party dependencies. Produces a single-page PDF
with invoice-like content (vendor, invoice number/date, line items, total) that
Azure AI Document Intelligence ``prebuilt-invoice`` and ``prebuilt-layout`` models
can analyze. Re-run this script to regenerate ``sample-invoice.pdf``.

    python generate-sample-invoice.py
"""

from __future__ import annotations

import pathlib

# Each tuple is (x, y, font_size, text). y grows upward from the page bottom.
LINES: list[tuple[int, int, int, str]] = [
    (72, 740, 20, "Contoso Office Supplies"),
    (72, 716, 11, "123 Market Street, Redmond, WA 98052"),
    (430, 740, 16, "INVOICE"),
    (430, 716, 11, "Invoice Number: INV-2026-00042"),
    (430, 700, 11, "Invoice Date: 2026-01-15"),
    (430, 684, 11, "Due Date: 2026-02-14"),
    (72, 660, 11, "Bill To:"),
    (72, 644, 11, "Fabrikam, Inc."),
    (72, 628, 11, "500 Aviation Way, Seattle, WA 98101"),
    (72, 584, 11, "Description                         Qty      Unit Price     Amount"),
    (72, 566, 11, "A4 Paper (case)                       10      $35.00        $350.00"),
    (72, 550, 11, "Toner Cartridge                        4      $89.50        $358.00"),
    (72, 534, 11, "Stapler                               12      $12.25        $147.00"),
    (72, 500, 11, "Subtotal: $855.00"),
    (72, 484, 11, "Tax (9.5%): $81.23"),
    (72, 468, 13, "Invoice Total: $936.23"),
    (72, 430, 11, "Remit payment to Contoso Office Supplies, Account 123456789."),
    (72, 414, 11, "Thank you for your business."),
]


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _content_stream() -> bytes:
    parts: list[str] = []
    for x, y, size, text in LINES:
        parts.append(f"BT /F1 {size} Tf {x} {y} Td ({_escape(text)}) Tj ET")
    return ("\n".join(parts) + "\n").encode("latin-1")


def build_pdf() -> bytes:
    content = _content_stream()
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n"
        + content
        + b"endstream",
    ]

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode("ascii") + body + b"\nendobj\n"

    xref_position = len(out)
    count = len(objects) + 1
    out += f"xref\n0 {count}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("ascii")
    out += (
        b"trailer\n<< /Size "
        + str(count).encode("ascii")
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_position).encode("ascii")
        + b"\n%%EOF\n"
    )
    return bytes(out)


def main() -> None:
    target = pathlib.Path(__file__).with_name("sample-invoice.pdf")
    target.write_bytes(build_pdf())
    print(f"Wrote {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

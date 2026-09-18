# Parent-private response encoding clarification

The outer response has exactly speak (boolean), message (string), and rationale
(string). The rationale MUST be a JSON-encoded string containing the existing
private metadata object, NOT a nested object in the outer response. Escape its
quotation marks correctly. This documents the unchanged existing parser; do not
normalize IDs, alter evidence, or relax any validator to make an answer pass.

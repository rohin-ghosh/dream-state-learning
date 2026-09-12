# Lossless P0 terminal capsule transport

The original archive exceeds GitHub's100MB single-file limit. Its exact bytes
are stored as ordered60MiB transport parts, not recompressed or resealed.

```
cat astra_P0_material_terminal_20260912.tgz.part00 astra_P0_material_terminal_20260912.tgz.part01 > /tmp/astra_P0_reconstructed.tgz
sha256sum /tmp/astra_P0_reconstructed.tgz
```

Expected complete SHA256:
`13ca1bcefa98d2c4336197f46093abe807f141b937aa5d3d78876ac58122c208`.
Part00: `88ca268c1f2912319f3c6f31c7e4e522a3433d07adb30bcd13c8524f6f01c4d8`.
Part01: `54c514597e29c209843d1c4ddfaf054c264e8eb4d71589a61301156eef753a26`.
Concatenation was independently hashed and matches the original archive.
The intact original remains at `/tmp/astra_P0_material_terminal_20260912.tgz`
and remote source evidence remains unchanged. All references to the logical
`.tgz` capsule in notes resolve through these parts.6024payloads were verified.

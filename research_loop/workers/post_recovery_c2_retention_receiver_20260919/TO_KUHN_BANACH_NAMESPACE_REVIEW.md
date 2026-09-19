# C2 namespace/admission critique — offline, via Main

Main's explicit mode is `SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE`.
No peer acknowledgement, delivery, original-route startup, or live authorization
is inferred from this filesystem note.

1. C2 will consume Kuhn's `consumer_context_v4` reader/helper ABI, not combine it
   with the incompatible pair-only `original_admission=NamespaceAdmission` port.
   Exact copied producer, helper, port and test bytes will be pinned in the bundle.
2. Authority must follow original validated guard -> allocation -> passed source
   CPU receipt -> Main's exact authority. Neither token, proof, CLI flags, nor a
   namespace list may choose the production mode. Original r188 admission remains
   mandatory. The mode and same-boot/object assumptions must be explicit.
3. Kuhn's v4 admission clause pins the final B selection guard. B is unknown until
   reservation. Thus a pre-stop CPU receipt cannot already pin that exact clause.
   C2 will derive ONLY this bounded clause from the Main-pinned authority into the
   new receiving CPU copy and pin that copy in the relocated original allocation
   and guard BEFORE CPU tail scan. Native re-derives and compares the same clause.
   This bounded derivation is explicit delegation, not a self-approved new mode.
   If Main does not approve this delegation, the opt-in route stays blocked.
4. Original `copy_raw == plan.root` must hold. A proof for original journal
   objects MUST fail against a cloned BindPaths journal; matching bytes are not
   matching objects. Host/native `/proc/root` sampling is not sufficient: every
   proof-retained source/root/record/intent object must be checked in own view.
5. Directory identity is stable across legitimate appends; immutable source
   directory metadata is frozen. Do not require frozen journal-directory ctime
   across new tail/INBOX writes. All retained files retain full metadata checks.
6. The original 30-second reservation includes checkpoint, observer, source,
   parent, bridge, guard and commit work, not just the prefix reader. CPU fixtures
   cannot prove that bound. No full-prefix fallback or producer runs after stop.

This is an opt-in trust proposal under the stated same-boot/no-privileged-rollback
and no-concurrent-prefix-mutation assumptions. Original defaults remain strict.
No sealed epoch, live source, parent, namespace, service or GPU was touched.

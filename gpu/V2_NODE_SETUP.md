# v2 node setup (one page)

## Lease criteria (Colossus search filters, in order)
1. GPU health = **Pass** (hard filter — reject any Fail/Warn)
2. Status = AVAILABLE (not RESERVED)
3. Production SKU — **avoid TS*/SIFX bring-up samples** (driver risk)
4. Preference: 8x H100/H200 > 4x > production B200 > 8x A100 (all fine)
5. >=32 CPU cores preferred (16 min), >=256GB RAM, >=1TB NVMe
6. OS: ubuntu-22.04 or 24.04 x86_64 standard
7. Pool max lease >= 7 days (run is hours; length is iteration room)

## Once leased
1. Add my key + create SSH wrapper (copy gpu/node_ssh.sh pattern, new IP).
2. Sync repo:   ./gpu/node_sync.sh   (or rsync -a --exclude .venv ~/dream-state)
3. On node:     bash gpu/v2_bootstrap.sh
   - checks nvidia-smi, builds venv on NVMe, pulls Qwen 7B + 0.5B,
     runs env sanity (960-ep life) + GPU smoke (0.5B end-to-end),
     prints the per-GPU worker plan.
4. Report back the bootstrap tail; harness workers launch per its plan.

Budget note (SPEC_V2 Part II §6): ~73M LLM tok/seed; 8 workers = full
5-seed v2.0 in hours on H100-class; reruns are cheap by design.

## GH200 (aarch64) setup recipe (learned 2026-08-21, lego-cg1-qct-034)
1. CLEAN image has no driver. Install: nvidia-headless-580-server-open
   + nvidia-utils-580-server (open module REQUIRED on Hopper/Grace).
2. CRITICAL: nvidia-smi shows "No devices found" / dmesg shows
   kmemsysNumaAddMemory failure until the kernel cmdline has
   `memhp_default_state=online_movable` (GH200 coherent-memory NUMA
   onlining). Add to GRUB_CMDLINE_LINUX_DEFAULT, update-grub, reboot.
3. CUDA keyring repo for ARM = ubuntu2404/sbsa (not x86_64).
4. torch: pip install torch --index-url .../whl/cu126 (aarch64 CUDA
   wheels exist). vLLM: try pip wheel first; fallback = HF backend.
5. vLLM aarch64 wheel is built for cu130: align with
   pip install --force-reinstall torch torchvision --index-url .../whl/cu130
   (+ nvidia-cuda-runtime-cu13; add its lib dir to LD_LIBRARY_PATH in the
   venv activate). VALIDATED end-to-end 2026-08-21 on lego-cg1-qct-034.

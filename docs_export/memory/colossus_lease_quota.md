---
name: colossus-lease-quota
description: "Colossus GPU lease quota is a rolling 30-day window, not a calendar-month reset"
metadata: 
  node_type: memory
  pinned: false
  originSessionId: d66e193e-e075-475c-96de-a582e32ee6c5
  modified: 2026-08-31T23:20:27.820Z
---

# Colossus lease usage quota (user-corrected)

While managing GPU leases for Rohin on NVIDIA's Colossus system, I claimed the
monthly lease-hours quota (1440 h) "resets tomorrow, Sep 1." Rohin checked the
actual policy and corrected me: **the quota is a rolling trailing-30-day
window, not a calendar-month counter.** September 1 does not zero it out;
headroom returns only as lease-hours older than 30 days age out of the window,
and ongoing leases keep consuming it in real time.

Other facts from that policy check (via Rohin): a quota increase can be
requested through Colossus Support. The quota counts wall-clock hours a lease
is held (booked hours, including future-dated bookings at creation time), not
GPU utilization — idle held nodes burn quota at the same rate as busy ones.

Lesson: never assume a "monthly quota" is calendar-based; verify the window
semantics before forecasting when capacity frees up, and forecast quota
recovery by computing when old lease-hours fall out of the trailing window.

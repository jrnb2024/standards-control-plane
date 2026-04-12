# Strategy — WP-SCP-011 Design-System Scaffolding and Evaluator Shell

**Work Package:** `WP-SCP-011`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Add a design-system shell that only flags obvious code-level drift:

- raw primitives where approved components should exist
- hard-coded visual values where tokens should exist
- action elements with no interactive-state markers

## 2. Why this slice now

The UX shell is live. The next pragmatic step is a similarly bounded design
shell so consult and audit can advise on obvious front-end drift before
product-level judgement arrives.

## 3. Delivery shape

- registry scaffolding first
- one failing design drift fixture
- one stable design fixture
- no screenshot or browser analysis
